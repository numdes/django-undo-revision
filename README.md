# django-undo-revision

**Atomic undo / rollback for Django models** — a reusable Django app that adds a "Ctrl+Z" undo button to your application data. Uses [django-simple-history](https://github.com/jazzband/django-simple-history) as its change-tracking engine.

```bash
pip install django-undo-revision
```

## What problem does it solve?

`django-simple-history` tracks every change to your models, but it doesn't give you a way to group multiple changes together and roll them all back at once. `django-undo-revision` adds that layer:

- A user edits a document, renames a tag, and reorders items — all in one request. One `undo_last_revision()` call rolls back all three changes atomically.
- You're building a collaborative editor, a project management tool, or any app where users need a reliable undo button.
- You want per-scope undo history (per user, per project, per session) rather than a single global history.

## How it works

Every mutation is wrapped in a **revision** — a named unit of work. A revision automatically captures all `django-simple-history` records (creates, updates, deletes) made within its context and groups them under a single `Revision` object. Calling `undo_last_revision(scope)` fetches the latest revision for a scope and replays all changes in reverse order inside a transaction.

```
open_revision(scope_id=...)
    └── saves Document        → Version(revision=R, object=doc_history_record)
    └── deletes Tag           → Version(revision=R, object=tag_history_record)
    └── updates Item.order    → Version(revision=R, object=item_history_record)

undo_last_revision(scope)
    └── restores Item.order   (reverse chronological)
    └── restores Tag
    └── restores Document
    └── deletes Revision R
```

## Requirements

| Dependency | Version |
|---|---|
| Python | ≥ 3.11 |
| Django | ≥ 4.2 (tested on 4.2, 5.0, 5.1) |
| django-simple-history | ≥ 3.11.0 |

## Installation

```bash
pip install django-undo-revision
```

Add to `INSTALLED_APPS` (order matters — `contenttypes` and `simple_history` must come first):

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

In `settings.py`, set the **scope model** — the entity that revisions are grouped under. This is typically your top-level container: a project, workspace, document, user, or session.

```python
# Required: the model that owns revisions
UNDO_REVISION_SCOPE_MODEL = "myapp.Project"

# URL kwarg used by UndoRevisionMixin to extract the scope id from the request
UNDO_REVISION_SCOPE_URL_KWARG = "project_id"

# HTTP methods that should automatically open a revision (default: all mutating methods)
UNDO_REVISION_HTTP_METHODS = ["post", "put", "patch", "delete"]
```

## Usage

### 1. Inherit models from `HistoricalModel`

```python
from django.db import models
from undo_revision.models import HistoricalModel


class Document(HistoricalModel):
    title = models.CharField(max_length=255)
    body = models.TextField()


class Tag(HistoricalModel):
    name = models.CharField(max_length=100)
    document = models.ForeignKey(Document, on_delete=models.CASCADE)
```

`HistoricalModel` wires up `RevisionHistoricalRecords` (an extended `HistoricalRecords`) and `RevisionQuerySet` as the default manager.

### 2. Wrap mutations in a revision

```python
from undo_revision.revision.context import open_revision

with open_revision(scope_id=project.id):
    document.title = "New title"
    document.save()

    tag.delete()

    Item.objects.bulk_update_with_history(items, fields=["order"])

# All changes are grouped into one revision.
# If nothing was saved inside the block, the revision is deleted automatically.
```

You can also attach to an existing revision by id (useful when a single logical action spans multiple functions):

```python
with open_revision(revision_id=existing_revision.id):
    ...
```

### 3. Undo the last revision

```python
from undo_revision.revision.undo import undo_last_revision, RevisionNotFoundError

try:
    undo_last_revision(scope=project)
except RevisionNotFoundError:
    # No revisions left — nothing to undo
    return Response({"detail": "Nothing to undo."}, status=400)
```

`undo_last_revision` runs inside a transaction. It rolls back all changes in reverse chronological order, then deletes the revision record.

### 4. Expose an undo endpoint (DRF example)

```python
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from undo_revision.revision.undo import undo_last_revision, RevisionNotFoundError


class ProjectViewSet(GenericViewSet):

    @action(detail=True, methods=["post"], url_path="undo")
    def undo(self, request, pk=None):
        project = self.get_object()
        try:
            undo_last_revision(scope=project)
        except RevisionNotFoundError:
            return Response({"detail": "Nothing to undo."}, status=400)
        return Response(status=204)
```

### 5. Auto-open revisions via mixin (DRF / CBV)

`UndoRevisionMixin` automatically wraps all mutating methods with `open_revision`, so you don't have to add the context manager to every view.

```python
from undo_revision.revision.mixins import UndoRevisionMixin
from rest_framework.viewsets import ModelViewSet


class DocumentViewSet(UndoRevisionMixin, ModelViewSet):
    queryset = Document.objects.all()
    serializer_class = DocumentSerializer
    scope_url_kwarg = "project_id"  # URL kwarg carrying the scope id
```

Every `POST`, `PUT`, `PATCH`, and `DELETE` request to this viewset will automatically open a revision scoped to `project_id`.

### 6. Bulk operations

`RevisionQuerySet` exposes helpers for bulk mutations that integrate with revision tracking:

```python
# Tracked — changes will be included in the current revision
MyModel.objects.bulk_create_with_history(objs)
MyModel.objects.bulk_update_with_history(objs, fields=["title", "order"])

# Untracked — changes are invisible to revision/undo
MyModel.objects.bulk_create_without_history(objs)
MyModel.objects.bulk_update_without_history(objs, fields=["title"])
MyModel.objects.create_without_history(title="...")
MyModel.objects.filter(...).delete_without_history()
```

Use the `_without_history` variants for seed data, migrations, or internal bookkeeping that shouldn't be undoable.

## Data model

```
Revision
  id          UUID  (PK)
  scope       FK → your scope model
  created_at  DateTimeField

Version
  id            UUID  (PK)
  revision      FK → Revision
  content_type  FK → ContentType
  object_id     TextField
  content_object GenericForeignKey → historical record (django-simple-history)
```

Each `Version` points to a `django-simple-history` historical record snapshot. On undo, the library reads back the pre-change field values from the snapshot and restores them.

## Key features

| Feature | Description |
|---|---|
| Atomic multi-model rollback | Group changes across many models into one revision and revert them all at once |
| Scoped undo history | Each scope (project, user, session) has its own independent undo stack |
| Bulk operation tracking | `bulk_create` and `bulk_update` are revision-aware out of the box |
| Zero-change revision cleanup | Revisions with no recorded changes are deleted automatically |
| DRF / CBV integration | Drop-in mixin auto-opens a revision per request |

## License

MIT
