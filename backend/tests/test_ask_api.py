from app.llm.base import LLMError, LLMRateLimitError
from app.llm.gemini import get_llm_provider
from app.main import app

LONG_TEXT = "Photosynthesis converts light energy into chemical energy stored in glucose."


class FailingProvider:
    def __init__(self, error):
        self.error = error

    def generate(self, system, prompt):
        raise self.error


def upload(client, path, name="notes.pdf"):
    with open(path, "rb") as f:
        return client.post("/api/documents", files={"file": (name, f, "application/pdf")})


def ask(client, question="What does photosynthesis make?", **extra):
    return client.post("/api/ask", json={"question": question, **extra})


def test_ask_returns_answer_with_citations(client, make_pdf):
    upload(client, make_pdf([LONG_TEXT]))

    response = ask(client)

    assert response.status_code == 200
    body = response.json()
    assert body["found"] is True
    assert body["answer"] == "Photosynthesis makes glucose. [1]"
    citation = body["citations"][0]
    assert (citation["ref"], citation["filename"], citation["page"]) == (1, "notes.pdf", 1)


def test_ask_reports_not_found(client, make_pdf, fake_llm):
    upload(client, make_pdf([LONG_TEXT]))
    fake_llm.answer = "NOT_FOUND"

    body = ask(client, "What is the capital of France?").json()

    assert body["found"] is False
    assert body["citations"] == []


def test_ask_without_documents_does_not_call_the_llm(client, fake_llm):
    response = ask(client)

    assert response.status_code == 200
    assert response.json()["found"] is False
    assert fake_llm.calls == []


def test_empty_question_is_rejected(client):
    response = ask(client, "   ")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMPTY_QUESTION"


def test_overlong_question_is_rejected(client):
    response = ask(client, "x" * 1001)

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "QUESTION_TOO_LONG"


def test_unknown_document_filter_returns_404(client, make_pdf):
    upload(client, make_pdf([LONG_TEXT]))

    response = ask(client, document_id="does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "DOCUMENT_NOT_FOUND"


def test_document_filter_limits_citations(client, make_pdf):
    upload(client, make_pdf([LONG_TEXT], name="a.pdf"), name="a.pdf")
    second_id = upload(client, make_pdf([LONG_TEXT], name="b.pdf"), name="b.pdf").json()["id"]

    body = ask(client, document_id=second_id).json()

    assert all(c["document_id"] == second_id for c in body["citations"])


def test_history_reaches_the_prompt(client, make_pdf, fake_llm):
    upload(client, make_pdf([LONG_TEXT]))

    ask(client, "Explain that more simply", history=[
        {"role": "user", "content": "What is photosynthesis?"},
        {"role": "assistant", "content": "A process in plants. [1]"},
    ])

    assert "User: What is photosynthesis?" in fake_llm.calls[0][1]


def test_rate_limit_becomes_429_with_retry_hint(client, make_pdf):
    upload(client, make_pdf([LONG_TEXT]))
    app.dependency_overrides[get_llm_provider] = lambda: FailingProvider(LLMRateLimitError())

    response = ask(client)

    assert response.status_code == 429
    error = response.json()["error"]
    assert error["code"] == "RATE_LIMITED"
    assert error["retry_after_seconds"] == 30


def test_llm_failure_becomes_502(client, make_pdf):
    upload(client, make_pdf([LONG_TEXT]))
    app.dependency_overrides[get_llm_provider] = lambda: FailingProvider(LLMError("boom"))

    response = ask(client)

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "LLM_ERROR"