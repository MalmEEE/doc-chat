import time
from functools import lru_cache

from google import genai
from google.genai import types

from app.config import get_settings
from app.llm.base import LLMError, LLMProvider, LLMRateLimitError


class GeminiProvider:
    def __init__(self, api_key: str, model: str, client=None,
                 max_retries: int = 2, base_delay: float = 2.0, sleep=time.sleep):
        self._client = client or genai.Client(api_key=api_key)
        self._model = model
        self._max_retries = max_retries
        self._base_delay = base_delay
        self._sleep = sleep

    def generate(self, system: str, prompt: str) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.2,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        for attempt in range(self._max_retries + 1):
            try:
                response = self._client.models.generate_content(
                    model=self._model, contents=prompt, config=config
                )
                return (response.text or "").strip()
            except Exception as exc:
                if getattr(exc, "code", None) == 429:
                    if attempt < self._max_retries:
                        self._sleep(self._base_delay * 2 ** attempt)   # 2 s, then 4 s
                        continue
                    raise LLMRateLimitError() from exc
                raise LLMError("The answer service is unavailable.") from exc
        raise LLMError("The answer service is unavailable.")


@lru_cache
def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    return GeminiProvider(api_key=settings.gemini_api_key, model=settings.llm_model)