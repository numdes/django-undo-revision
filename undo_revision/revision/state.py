import contextvars

from uuid import UUID


revision_id_ctx_var: contextvars.ContextVar[UUID | None] = contextvars.ContextVar("revision", default=None)
