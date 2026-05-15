import pytest

from tests.models import Document
from tests.models import Project
from undo_revision.revision.cleanup import cleanup_revisions
from undo_revision.models import Revision
from undo_revision.models import Version

pytestmark = pytest.mark.django_db


@pytest.fixture
def project():
    return Project.objects.create()


def test_cleanup(project):
    docs = [Document(project=project, title=f"doc_{i}") for i in range(3)]
    Document.objects.bulk_create_with_history(docs)

    cleanup_revisions()

    for doc in docs:
        assert doc.history.count() == 0
    assert Revision.objects.count() == 0
    assert Version.objects.count() == 0

