import pytest

from app.services.documents_repo import Document, DocumentsRepo


def make_doc(doc_id="doc-1", uploaded_at="2026-10-01T10:00:00Z"):
    return Document(
        id=doc_id,
        filename=f"{doc_id}.pdf",
        stored_path=f"data/uploads/{doc_id}.pdf",
        pages=10,
        chunks=25,
        uploaded_at=uploaded_at,
    )


@pytest.fixture
def repo(tmp_path):
    return DocumentsRepo(str(tmp_path / "test.db"))


def test_new_repo_is_empty(repo):
    assert repo.list() == []


def test_added_document_can_be_fetched(repo):
    doc = make_doc()
    repo.add(doc)

    assert repo.get("doc-1") == doc


def test_get_returns_none_for_unknown_id(repo):
    assert repo.get("missing") is None


def test_list_returns_newest_first(repo):
    repo.add(make_doc("old", "2026-10-01T10:00:00Z"))
    repo.add(make_doc("new", "2026-10-02T10:00:00Z"))

    assert [d.id for d in repo.list()] == ["new", "old"]


def test_delete_removes_document_and_reports_result(repo):
    repo.add(make_doc())

    assert repo.delete("doc-1") is True
    assert repo.get("doc-1") is None
    assert repo.delete("doc-1") is False


def test_documents_survive_reopening_the_database(tmp_path):
    path = str(tmp_path / "test.db")
    DocumentsRepo(path).add(make_doc())

    assert DocumentsRepo(path).get("doc-1") is not None