import pytest

from app.llm.base import LLMError, LLMRateLimitError
from app.llm.fake import FakeProvider
from app.llm.gemini import GeminiProvider


class RateLimited(Exception):
    code = 429


class StubResponse:
    def __init__(self, text):
        self.text = text


class StubModels:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    def generate_content(self, **kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class StubClient:
    def __init__(self, outcomes):
        self.models = StubModels(outcomes)


def make_provider(outcomes):
    client = StubClient(outcomes)
    provider = GeminiProvider(api_key="test", model="test-model", client=client, sleep=lambda s: None)
    return provider, client


def test_returns_stripped_answer_text():
    provider, _ = make_provider([StubResponse("  An answer. [1]  ")])

    assert provider.generate("system", "prompt") == "An answer. [1]"


def test_retries_after_rate_limit_then_succeeds():
    provider, client = make_provider([RateLimited(), StubResponse("ok")])

    assert provider.generate("system", "prompt") == "ok"
    assert client.models.calls == 2


def test_raises_rate_limit_error_when_retries_run_out():
    provider, client = make_provider([RateLimited(), RateLimited(), RateLimited()])

    with pytest.raises(LLMRateLimitError):
        provider.generate("system", "prompt")
    assert client.models.calls == 3


def test_other_failures_raise_llm_error_without_retrying():
    provider, client = make_provider([RuntimeError("boom")])

    with pytest.raises(LLMError):
        provider.generate("system", "prompt")
    assert client.models.calls == 1


def test_fake_provider_returns_canned_answer_and_records_calls():
    fake = FakeProvider(answer="Hello [1]")

    assert fake.generate("sys", "question") == "Hello [1]"
    assert fake.calls == [("sys", "question")]