from collections.abc import Callable
from functools import wraps

from django.conf import settings

from undo_revision.revision.context import open_revision


REVISION_HTTP_METHODS = getattr(settings, "UNDO_REVISION_HTTP_METHODS", None) or ["post", "put", "patch", "delete"]


class UndoRevisionMixin:
    project_url_kwarg: str | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        project_url_kwarg = self.project_url_kwarg or settings.UNDO_REVISION_PROJECT_URL_KWARG
        for http_method in REVISION_HTTP_METHODS:
            if hasattr(self, http_method):
                setattr(self, http_method, _wrap_with_new_revision(getattr(self, http_method), project_url_kwarg))


def _wrap_with_new_revision(func: Callable, project_url_kwarg: str | None) -> Callable:
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        assert project_url_kwarg in kwargs
        with open_revision(project_id=kwargs[project_url_kwarg]):
            return func(request, *args, **kwargs)

    return wrapper
