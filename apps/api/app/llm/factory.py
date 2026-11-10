from app.core.config import get_settings
from app.llm.base import LLMNotConfigured, LLMProvider
from app.llm.fake import FakeProvider
from app.llm.groq import GroqProvider


def get_llm_provider() -> LLMProvider:
    """FastAPI dependency. Tests override it. Raises LLMNotConfigured when no key/model is set."""
    s = get_settings()
    if s.llm_provider == "fake":
        return FakeProvider()
    return GroqProvider(
        s.groq_api_key,
        s.llm_model_primary,
        s.groq_base_url,
        s.llm_timeout_seconds,
        max_tokens=s.llm_max_output,
        reasoning_effort=s.llm_reasoning_effort,
        fallback_model=s.llm_model_fallback,
        retries=s.llm_retries,
    )


__all__ = ["LLMNotConfigured", "get_llm_provider"]
