import logging

from django.db import transaction


logger = logging.getLogger(__name__)

# django-simple-history history_type codes (simple_history/models.py CharField choices)
HISTORY_TYPE_CHANGED = "~"
HISTORY_TYPE_CREATED = "+"
HISTORY_TYPE_DELETED = "-"


class RevisionNotFoundError(Exception):
    pass


@transaction.atomic
def undo_last_revision(scope):
    revision = scope.revision_set.order_by("created_at").last()
    if revision is None:
        logger.debug("No revisions found for scope id %s", scope.id)
        raise RevisionNotFoundError(f"Revision not found for scope id={scope.id}.")

    content_objs = [v.content_object for v in revision.version_set.all()]
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Undoing revision %s for scope id %s. Found %s content objects: %s",
            revision.id,
            scope.id,
            len(content_objs),
            ", ".join(
                f"{i}.{o.instance.__class__.__name__} '{o.history_type}'" for i, o in enumerate(content_objs, start=1)
            ),
        )
    for content_obj in sorted(content_objs, key=lambda v: v.history_date, reverse=True):
        instance = content_obj.instance
        history_type = content_obj.history_type
        if history_type == HISTORY_TYPE_CHANGED:
            instance._state.adding = False
            instance.save_without_historical_record()
        elif history_type == HISTORY_TYPE_CREATED:
            instance.skip_history_when_saving = True
            try:
                instance.delete()
            finally:
                del instance.skip_history_when_saving
        elif history_type == HISTORY_TYPE_DELETED:
            instance.save_without_historical_record()
        else:
            raise TypeError(f"Unknown history type: {content_obj.history_type}")

    logger.debug("Deleting revision %s for scope id %s", revision.id, scope.id)
    revision.delete()
