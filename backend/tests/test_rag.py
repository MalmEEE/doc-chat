import pytest

from app.llm.fake import FakeProvider
from app.services.chunking import Chunk
from app.services.rag import NO_DOCUMENTS_MESSAGE, NOT_FOUND_MESSAGE, answer_question
from app.services.vector_store import VectorStore

CHUNKS = [
    Chunk(page=1, index=0, text="Cats are mammals."),
    Chunk(page=2, index=0, text="Taxes are due in April."),
]
VECTORS = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]]
HISTORY = [("user", "What is a cat?"), ("assistant", "A mammal. [1]")]

def fake_embed(texts):
    """Every question points at the 'cats' chunk, so it is always retrieved first."""
    return [[1.0, 0.0, 0.0] for _ in texts]


@pytest.fixture
def store(tmp_path):
    store = VectorStore(str(tmp_path / "chroma"))
    store.add("doc-a", "a.pdf", CHUNKS, VECTORS)
    return store


def ask(store, llm, **kwargs):
    return answer_question(
        question="What are cats?", store=store, llm=llm, top_k=8, embed=fake_embed, **kwargs
    )


def test_answer_includes_citation_details(store):
    result = ask(store, FakeProvider("Cats are mammals. [1]"))

    assert result.found is True
    assert result.answer == "Cats are mammals. [1]"
    assert len(result.citations) == 1
    citation = result.citations[0]
    assert (citation.ref, citation.filename, citation.page) == (1, "a.pdf", 1)
    assert citation.document_id == "doc-a"
    assert citation.snippet == "Cats are mammals."


def test_only_cited_chunks_are_returned_once_in_order(store):
    result = ask(store, FakeProvider("Taxes first. [2] Then cats. [1][2]"))

    assert [c.ref for c in result.citations] == [2, 1]


def test_not_found_sentinel_gives_friendly_message_and_no_citations(store):
    result = ask(store, FakeProvider("NOT_FOUND"))

    assert result.found is False
    assert result.answer == NOT_FOUND_MESSAGE
    assert result.citations == []


def test_citation_numbers_out_of_range_are_ignored(store):
    result = ask(store, FakeProvider("An answer. [7] [1]"))

    assert [c.ref for c in result.citations] == [1]


def test_answer_without_citations_falls_back_to_top_chunk(store):
    result = ask(store, FakeProvider("Cats are mammals."))

    assert result.found is True
    assert [c.ref for c in result.citations] == [1]


def test_empty_store_asks_for_an_upload_without_calling_the_llm(tmp_path):
    llm = FakeProvider("should not be used")

    result = ask(VectorStore(str(tmp_path / "empty")), llm)

    assert result.found is False
    assert result.answer == NO_DOCUMENTS_MESSAGE
    assert llm.calls == []


def test_document_filter_limits_citations_to_that_document(store):
    store.add("doc-b", "b.pdf", CHUNKS, VECTORS)

    result = ask(store, FakeProvider("Cats are mammals. [1]"), document_id="doc-b")

    assert result.citations[0].document_id == "doc-b"


def test_prompt_sent_to_llm_contains_question_and_context(store):
    llm = FakeProvider("Cats are mammals. [1]")

    ask(store, llm)

    system, prompt = llm.calls[0]
    assert "What are cats?" in prompt
    assert "Cats are mammals." in prompt
    assert "NOT_FOUND" in system


def recording_embed(seen):
    def embed(texts):
        seen.extend(texts)
        return [[1.0, 0.0, 0.0] for _ in texts]
    return embed


def test_history_is_included_in_the_prompt(store):
    llm = FakeProvider("Cats are mammals. [1]")

    ask(store, llm, history=HISTORY)

    assert "User: What is a cat?" in llm.calls[0][1]


def test_previous_question_is_added_to_the_retrieval_query(store):
    seen = []

    answer_question(
        question="Explain that more simply", store=store, llm=FakeProvider("Simple. [1]"),
        top_k=8, history=HISTORY, embed=recording_embed(seen),
    )

    assert seen == ["What is a cat? Explain that more simply"]


def test_without_history_only_the_question_is_embedded(store):
    seen = []

    answer_question(
        question="What are cats?", store=store, llm=FakeProvider("Mammals. [1]"),
        top_k=8, embed=recording_embed(seen),
    )

    assert seen == ["What are cats?"]


def test_only_the_last_six_history_messages_are_used(store):
    llm = FakeProvider("Cats are mammals. [1]")
    history = [("user", f"question {i}") for i in range(10)]

    ask(store, llm, history=history)

    prompt = llm.calls[0][1]
    assert "question 3" not in prompt
    assert "question 4" in prompt