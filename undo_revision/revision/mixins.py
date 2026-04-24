from collections.abc import Callable
from functools import wraps

from django.conf import settings

from undo_revision.revision.context import open_revision


REVISION_HTTP_METHODS = getattr(settings, "UNDO_REVISION_HTTP_METHODS", ["post", "put", "patch", "delete"])


class UndoRevisionMixin:
    scope_url_kwarg: str | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        scope_url_kwarg = self.scope_url_kwarg or getattr(settings, "UNDO_REVISION_SCOPE_URL_KWARG", None)
        for http_method in REVISION_HTTP_METHODS:
            if hasattr(self, http_method):
                setattr(self, http_method, _wrap_with_new_revision(getattr(self, http_method), scope_url_kwarg))


def _wrap_with_new_revision(func: Callable, scope_url_kwarg: str | None) -> Callable:
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        if scope_url_kwarg not in kwargs:
            raise KeyError(
                f"URL kwarg '{scope_url_kwarg}' not found in kwargs. "
                "Check that the URL pattern includes this kwarg and that "
                "UndoRevisionMixin.scope_url_kwarg (or UNDO_REVISION_SCOPE_URL_KWARG) is set correctly."
            )
        with open_revision(scope_id=kwargs[scope_url_kwarg]):
            return func(request, *args, **kwargs)

    return wrapper
