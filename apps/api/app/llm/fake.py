from collections.abc import Callable

from app.llm.base import LLMUnavailable


class FakeProvider:
    """Scripted provider for tests and offline development. It never calls a network and is selected only with LLM_PROVIDER=fake."""

    name = "fake"
    model = "fake-model"

    def __init__(self, responses: list[str] | Callable[[list[dict[str, str]]], str] | None = None):
        self.responses = responses if responses is not None else []
        self.calls: list[list[dict[str, str]]] = []

    def complete_json(self, messages: list[dict[str, str]]) -> str:
        self.calls.append(messages)
        if callable(self.responses):
            return self.responses(messages)
        if not self.responses:
            raise LLMUnavailable("Fake provider has no scripted response.")
        return self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
