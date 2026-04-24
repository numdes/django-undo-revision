import pytest

from tests.models import Document
from tests.models import Project
from undo_revision.models import Revision
from undo_revision.revision.context import open_revision
from undo_revision.revision.state import revision_id_ctx_var


pytestmark = pytest.mark.django_db


@pytest.fixture
def project():
    return Project.objects.create()


def test_creates_revision(project):
    with open_revision(project_id=project.id) as revision:
        Document.objects.create(project=project, title="test")

    assert Revision.objects.filter(id=revision.id).exists()


def test_deletes_empty_revision(project):
    with open_revision(project_id=project.id) as revision:
        revision_id = revision.id

    assert not Revision.objects.filter(id=revision_id).exists()


def test_reuses_existing_revision(project):
    with open_revision(project_id=project.id) as revision:
        Document.objects.create(project=project, title="v1")

    with open_revision(revision_id=revision.id) as revision2:
        Document.objects.create(project=project, title="v2")

    expected_version_count = 2
    assert revision2.id == revision.id
    assert revision2.version_set.count() == expected_version_count


def test_raises_with_both_ids(project):
    with pytest.raises(ValueError), open_revision(project_id=project.id, revision_id=project.id):
        pass


def test_raises_without_ids():
    with pytest.raises(ValueError), open_revision():
        pass


def test_sets_ctx_var(project):
    assert revision_id_ctx_var.get() is None

    with open_revision(project_id=project.id) as revision:
        Document.objects.create(project=project, title="test")
        assert revision_id_ctx_var.get() == revision.id

    assert revision_id_ctx_var.get() is None


def test_resets_ctx_var_on_exception(project):
    with pytest.raises(RuntimeError), open_revision(project_id=project.id):
        Document.objects.create(project=project, title="test")
        raise RuntimeError

    assert revision_id_ctx_var.get() is None
