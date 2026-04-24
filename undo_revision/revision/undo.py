import logging

from deepdiff.model import DoesNotExist
from django.db import transaction


logger = logging.getLogger(__name__)


class RevisionNotFoundError(Exception):
    pass


@transaction.atomic
def undo_last_revision(project):
    revision = project.revision_set.order_by("created_at").last()
    if revision is None:
        logger.debug("No revisions found for project id %s", project.id)
        raise RevisionNotFoundError(f"Revision not found for project id={project.id}.")

    content_objs = [v.content_object for v in revision.version_set.all()]
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(
            "Undoing revision %s for project id %s. Found %s content objects: %s",
            revision.id,
            project.id,
            len(content_objs),
            "".join([
                f"{i}.{o.instance.__class__.__name__} '{o.history_type}' " for i, o in enumerate(content_objs, start=1)
            ]),
        )
    for content_obj in sorted(content_objs, key=lambda v: v.history_date, reverse=True):
        instance = content_obj.instance
        match content_obj.history_type:
            case "~":
                instance._state.adding = False
                instance.save_without_historical_record()
            case "+":
                instance.skip_history_when_saving = True
                try:
                    instance.delete()
                except DoesNotExist:
                    logger.debug("Instance not found for deletion: %s. Skipping.", instance)
                finally:
                    del instance.skip_history_when_saving
            case "-":
                instance.save_without_historical_record()
            case _:
                raise TypeError(f"Unknown history type: {content_obj.history_type}")

    logger.debug("Deleting revision %s for project id %s", revision.id, project.id)
    revision.delete()
