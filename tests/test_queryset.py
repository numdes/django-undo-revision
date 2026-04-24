import pytest

from tests.models import Document
from tests.models import Project


pytestmark = pytest.mark.django_db


@pytest.fixture
def project():
    return Project.objects.create()


def test_create_without_history(project):
    doc = Document.objects.create_without_history(project=project, title="test")

    assert doc.history.count() == 0


def test_delete_without_history(project):
    doc = Document.objects.create(project=project, title="test")
    history_count = doc.history.count()

    Document.objects.filter(id=doc.id).delete_without_history()

    assert doc.history.count() == history_count


def test_bulk_create_with_history(project):
    docs = [Document(project=project, title=f"doc_{i}") for i in range(3)]
    Document.objects.bulk_create_with_history(docs)

    for doc in docs:
        assert doc.history.count() == 1


def test_bulk_update_with_history(project):
    doc = Document.objects.create(project=project, title="original")
    doc.title = "updated"

    Document.objects.bulk_update_with_history([doc], ["title"])

    expected_history_count = 2
    assert doc.history.count() == expected_history_count


def test_bulk_create_without_history(project):
    docs = [Document(project=project, title=f"doc_{i}") for i in range(3)]
    Document.objects.bulk_create_without_history(docs)

    for doc in docs:
        assert doc.history.count() == 0


def test_bulk_update_without_history(project):
    doc = Document.objects.create(project=project, title="original")
    doc.title = "updated"

    Document.objects.bulk_update_without_history([doc], ["title"])

    assert doc.history.count() == 1
