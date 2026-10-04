from typing import Protocol


class LLMProvider(Protocol):
    """Anything with this method can be used as the app's LLM (NFR-6)."""

    def generate(self, system: str, prompt: str) -> str: ...


class LLMError(Exception):
    """The LLM call failed."""


class LLMRateLimitError(LLMError):
    """The LLM is rate limited, even after retries."""

    def __init__(self, retry_after_seconds: int = 30):
        super().__init__("Rate limited")
        self.retry_after_seconds = retry_after_seconds