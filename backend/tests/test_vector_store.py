import pytest

from app.services.chunking import Chunk
from app.services.vector_store import VectorStore

CHUNKS = [
    Chunk(page=1, index=0, text="about cats"),
    Chunk(page=2, index=0, text="about taxes"),
]
VECTORS = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]


@pytest.fixture
def store(tmp_path):
    return VectorStore(str(tmp_path / "chroma"))


def test_query_on_empty_store_returns_nothing(store):
    assert store.query([1.0, 0.0, 0.0], top_k=5) == []


def test_query_returns_closest_chunk_first_with_metadata(store):
    store.add("doc-a", "a.pdf", CHUNKS, VECTORS)

    results = store.query([1.0, 0.0, 0.0], top_k=2)

    assert len(results) == 2
    assert results[0].text == "about cats"
    assert results[0].page == 1
    assert results[0].filename == "a.pdf"
    assert results[0].document_id == "doc-a"
    assert results[0].distance < results[1].distance


def test_query_can_be_limited_to_one_document(store):
    store.add("doc-a", "a.pdf", CHUNKS, VECTORS)
    store.add("doc-b", "b.pdf", CHUNKS, VECTORS)

    results = store.query([1.0, 0.0, 0.0], top_k=4, document_id="doc-b")

    assert results
    assert all(r.document_id == "doc-b" for r in results)


def test_delete_document_removes_only_that_document(store):
    store.add("doc-a", "a.pdf", CHUNKS, VECTORS)
    store.add("doc-b", "b.pdf", CHUNKS, VECTORS)

    store.delete_document("doc-a")

    assert store.count() == 2
    assert all(r.document_id == "doc-b" for r in store.query([1.0, 0.0, 0.0], top_k=4))


def test_data_survives_reopening_the_store(tmp_path):
    path = str(tmp_path / "chroma")
    VectorStore(path).add("doc-a", "a.pdf", CHUNKS, VECTORS)

    reopened = VectorStore(path)

    assert reopened.count() == 2