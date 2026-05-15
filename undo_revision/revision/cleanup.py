import logging

from django.apps import apps
from django.db import transaction
from undo_revision.models import Revision, Version, HistoricalModel

logger = logging.getLogger(__name__)


@transaction.atomic
def cleanup_revisions() -> None:
    logger.info("Starting cleanup")

    versions_deleted, _ = Version.objects.all().delete()
    revisions_deleted, _ = Revision.objects.all().delete()

    logger.info(
        "Deleted versions=%s revisions=%s",
        versions_deleted,
        revisions_deleted,
    )

    historical_deleted_total = 0

    for model in apps.get_models():
        if not issubclass(model, HistoricalModel):
            continue

        history_model = getattr(model.history, "model", None)
        if history_model is None:
            continue

        deleted_count, _ = history_model.objects.all().delete()
        historical_deleted_total += deleted_count

        logger.info(
            "Deleted historical records: model=%s count=%s",
            model.__name__,
            deleted_count,
        )

    logger.info(
        "Cleanup finished. Total historical deleted=%s",
        historical_deleted_total,
    )