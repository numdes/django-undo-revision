import contextlib

from collections.abc import Generator
from typing import overload
from uuid import UUID

from undo_revision.models import Revision
from undo_revision.revision.state import revision_id_ctx_var


@overload
def open_revision(*, project_id: UUID) -> contextlib.AbstractContextManager[Revision]: ...
@overload
def open_revision(*, revision_id: UUID) -> contextlib.AbstractContextManager[Revision]: ...


@contextlib.contextmanager
def open_revision(
    *, project_id: UUID | None = None, revision_id: UUID | None = None
) -> Generator[Revision, None, None]:
    if project_id is not None and revision_id is not None:
        raise ValueError("Нельзя передать одновременно project_id и revision_id")

    if revision_id is not None:
        revision = Revision.objects.get(id=revision_id)
    elif project_id is not None:
        revision = Revision.objects.create(project_id=project_id)
    else:
        raise ValueError("Нужно передать project_id или revision_id")

    token = revision_id_ctx_var.set(revision.id)
    try:
        yield revision
    finally:
        revision_id_ctx_var.reset(token)
        if not revision.version_set.exists():
            revision.delete()
