# django-undo-revision

A Django reusable app for revision-based undo functionality, built on top of [django-simple-history](https://github.com/jazzband/django-simple-history).

## How it works

Every mutation is wrapped in a **revision** — a unit that can be rolled back atomically with a single `undo_last_revision(scope)` call. A revision automatically groups all historical records (creates, updates, deletes) made within its context.

## Installation

```bash
pip install django-undo-revision
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "django.contrib.contenttypes",
    "simple_history",
    "undo_revision",
]
```

Run migrations:

```bash
python manage.py migrate
```

## Configuration

In `settings.py`, set the scope model (the entity revisions are scoped to — can be a project, user, session, or any model):

```python
UNDO_REVISION_SCOPE_MODEL = "myapp.Project"  # required

# URL kwarg used by UndoRevisionMixin to extract the scope id
UNDO_REVISION_SCOPE_URL_KWARG = "project_id"

# HTTP methods that should open a revision (default: all mutating methods)
UNDO_REVISION_HTTP_METHODS = ["post", "put", "patch", "delete"]
```

## Usage

### 1. Inherit models from `HistoricalModel`

```python
from undo_revision.models import HistoricalModel


class Document(HistoricalModel):
    title = models.CharField(max_length=255)
    body = models.TextField()
```

`HistoricalModel` wires up `RevisionHistoricalRecords` (an extension of `HistoricalRecords`) and `RevisionQuerySet`.

### 2. Open a revision around mutations

```python
from undo_revision.revision.context import open_revision

with open_revision(scope_id=project.id):
    doc.title = "New title"
    doc.save()
    other_obj.delete()
# All changes inside the block are grouped into one revision
```

If no changes were recorded inside the block, the revision is deleted automatically.

### 3. Undo the last revision

```python
from undo_revision.revision.undo import undo_last_revision, RevisionNotFoundError

try:
    undo_last_revision(scope=project)
except RevisionNotFoundError:
    print("Nothing to undo")
```

The function fetches the latest revision for the scope and rolls back all its changes in reverse chronological order.

### 4. Auto-open revisions via mixin (DRF / CBV)

```python
from undo_revision.revision.mixins import UndoRevisionMixin
from rest_framework.viewsets import ModelViewSet


class DocumentViewSet(UndoRevisionMixin, ModelViewSet):
    scope_url_kwarg = "project_id"  # URL kwarg carrying the scope id
    ...
```

The mixin wraps all mutating methods (`post`, `put`, `patch`, `delete`) with `open_revision` automatically.

### 5. Bulk operations

`RevisionQuerySet` exposes helpers for bulk mutations:

```python
MyModel.objects.bulk_create_with_history(objs)
MyModel.objects.bulk_update_with_history(objs, fields=["title"])

# Skip history (not tracked in any revision)
MyModel.objects.bulk_create_without_history(objs)
MyModel.objects.bulk_update_without_history(objs, fields=["title"])
MyModel.objects.create_without_history(title="...")
MyModel.objects.filter(...).delete_without_history()
```

## License

MIT