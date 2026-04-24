import uuid

from django.db import models

from undo_revision.models import HistoricalModel


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    class Meta:
        app_label = "tests"

    def __str__(self) -> str:
        return str(self.id)


class Document(HistoricalModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)

    class Meta:
        app_label = "tests"
