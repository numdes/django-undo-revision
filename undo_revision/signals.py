from django.dispatch import receiver
from simple_history.signals import post_create_historical_record

from undo_revision.models import VersionsHistoricalModel
from undo_revision.revision.state import revision_id_ctx_var


@receiver(post_create_historical_record)
def post_create_historical_record_callback(sender, history_instance: VersionsHistoricalModel, **kwargs):
    revision_id = revision_id_ctx_var.get()
    if revision_id is not None:
        history_instance.versions.create(revision_id=revision_id)
