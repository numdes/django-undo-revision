from django.apps import AppConfig


class UndoRevisionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "undo_revision"

    def ready(self):
        from . import signals  # noqa: F401, PLC0415
