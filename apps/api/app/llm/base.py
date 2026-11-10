from typing import Protocol


class LLMError(Exception):
    """Base class. Messages never contain keys or user content."""


class LLMNotConfigured(LLMError):
    pass


class LLMRateLimited(LLMError):
    def __init__(self, retry_after: int | None = None):
        super().__init__("The AI provider rate limit was reached.")
        self.retry_after = retry_after


class LLMUnavailable(LLMError):
    pass


class LLMInvalidOutput(LLMError):
    pass


class LLMProvider(Protocol):
    name: str
    model: str

    def complete_json(self, messages: list[dict[str, str]]) -> str:
        """Return the model's raw text, which should be one JSON object. Raises an LLMError subclass on failure."""
        ...
