__all__ = [
    "HistoricalModel",
    "Revision",
    "Version",
    "VersionsHistoricalModel",
]

import uuid

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db import transaction
from django.db.models.signals import pre_save
from simple_history.manager import HistoryManager
from simple_history.models import HistoricalRecords
from simple_history.utils import bulk_create_with_history
from simple_history.utils import get_history_manager_for_model
from typing_extensions import override

from undo_revision.revision.state import revision_id_ctx_var


class Revision(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    created_at = models.DateTimeField(auto_now_add=True)
    scope = models.ForeignKey(settings.UNDO_REVISION_SCOPE_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.pk)


class Version(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    revision = models.ForeignKey(Revision, on_delete=models.CASCADE)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.TextField()
    content_object = GenericForeignKey()

    def __str__(self):
        return str(self.pk)


class RevisionHistoryManager(HistoryManager):
    @override
    def bulk_history_create(
        self,
        objs,
        batch_size=None,
        update=False,
        default_user=None,
        default_change_reason="",
        default_date=None,
        custom_historical_attrs=None,
    ):
        with transaction.atomic(savepoint=False):
            history_objs = super().bulk_history_create(
                objs,
                batch_size,
                update,
                default_user,
                default_change_reason,
                default_date,
                custom_historical_attrs,
            )

            revision_id = revision_id_ctx_var.get()
            versions = []
            if revision_id is not None:
                versions = [
                    Version(
                        revision_id=revision_id,
                        content_type=ContentType.objects.get_for_model(history_obj),
                        object_id=history_obj.pk,
                    )
                    for history_obj in history_objs
                ]
            Version.objects.bulk_create(versions)


class VersionsHistoricalModel(models.Model):
    versions = GenericRelation(Version)

    class Meta:
        abstract = True


class RevisionQuerySet(models.QuerySet):
    def delete_without_history(self):
        self._skip_simple_history_delete = True
        return self.delete()

    def create_without_history(self, **kwargs):
        self.model.skip_history_when_saving = True
        res = super().create(**kwargs)
        del self.model.skip_history_when_saving
        return res

    def bulk_create_with_history(self, objs):
        return bulk_create_with_history(objs, self.model)

    def bulk_update_with_history(self, objs, fields):
        with transaction.atomic(savepoint=False):
            old_objs = list(self.filter(pk__in=[obj.pk for obj in objs]))  # important to be before bulk_update
            rows_updated = self.bulk_update(objs, fields)

            history_manager = get_history_manager_for_model(self.model)
            history_manager.bulk_history_create(old_objs, update=True)

        return rows_updated

    def bulk_create_without_history(
        self,
        objs,
        batch_size=None,
        ignore_conflicts=False,
        update_conflicts=False,
        update_fields=None,
        unique_fields=None,
    ):
        self._skip_simple_history_create = True
        return self.bulk_create(
            objs,
            batch_size,
            ignore_conflicts,
            update_conflicts,
            update_fields,
            unique_fields,
        )

    def bulk_update_without_history(self, objs, fields, batch_size=None):
        self._skip_simple_history_create = True
        return self.bulk_update(objs, fields, batch_size)


class RevisionHistoricalRecords(HistoricalRecords):
    _old_instance_attr = "_simple_history_old_instance"

    def finalize(self, sender, **kwargs):
        super().finalize(sender, **kwargs)
        pre_save.connect(self.capture_old_instance, sender=sender, weak=False)

    def capture_old_instance(self, instance, raw=False, using=None, **kwargs):
        if raw or instance._state.adding or not instance.pk:
            return

        model = type(instance)
        try:
            old = model._default_manager.using(using).get(pk=instance.pk)
        except model.DoesNotExist:
            return

        setattr(instance, self._old_instance_attr, old)

    def post_delete(self, instance, using=None, **kwargs):
        origin = kwargs.get("origin")

        if getattr(origin, "_skip_simple_history_delete", False):
            return

        super().post_delete(instance, using=using, **kwargs)

    def post_save(self, instance, created, raw=False, using=None, **kwargs):
        if raw:
            return

        origin = kwargs.get("origin")

        if getattr(origin, "_skip_simple_history_create", False):
            return

        if not created:
            if getattr(instance, "skip_history_when_saving", False):
                return

            old = getattr(instance, self._old_instance_attr)
            instance = old

        try:
            super().post_save(instance, created, using=using, **kwargs)
        finally:
            if hasattr(instance, self._old_instance_attr):
                delattr(instance, self._old_instance_attr)


class HistoricalModel(models.Model):
    history = RevisionHistoricalRecords(
        bases=[VersionsHistoricalModel],
        inherit=True,
        history_manager=RevisionHistoryManager,
    )
    objects = RevisionQuerySet.as_manager()

    class Meta:
        abstract = True
