import pytest

from tests.models import Document
from tests.models import Project
from undo_revision.models import Revision
from undo_revision.revision.context import open_revision
from undo_revision.revision.undo import RevisionNotFoundError
from undo_revision.revision.undo import undo_last_revision


pytestmark = pytest.mark.django_db


@pytest.fixture
def project():
    return Project.objects.create()


def test_undo_create(project):
    with open_revision(scope_id=project.id):
        doc = Document.objects.create(project=project, title="new")

    undo_last_revision(project)

    assert not Document.objects.filter(id=doc.id).exists()


def test_undo_update(project):
    doc = Document.objects.create(project=project, title="original")

    with open_revision(scope_id=project.id):
        doc.title = "updated"
        doc.save()

    undo_last_revision(project)

    doc.refresh_from_db()
    assert doc.title == "original"


def test_undo_delete(project):
    doc = Document.objects.create(project=project, title="to_delete")
    doc_id = doc.id

    with open_revision(scope_id=project.id):
        doc.delete()

    undo_last_revision(project)

    assert Document.objects.filter(id=doc_id).exists()


def test_undo_raises_if_no_revision(project):
    with pytest.raises(RevisionNotFoundError):
        undo_last_revision(project)


def test_undo_deletes_revision(project):
    with open_revision(scope_id=project.id) as revision:
        Document.objects.create(project=project, title="test")

    undo_last_revision(project)

    assert not Revision.objects.filter(id=revision.id).exists()


def test_undo_multiple_objects(project):
    doc1 = Document.objects.create(project=project, title="a")
    doc2 = Document.objects.create(project=project, title="b")

    with open_revision(scope_id=project.id):
        doc1.title = "a_updated"
        doc1.save()
        doc2.title = "b_updated"
        doc2.save()

    undo_last_revision(project)

    doc1.refresh_from_db()
    doc2.refresh_from_db()
    assert doc1.title == "a"
    assert doc2.title == "b"
