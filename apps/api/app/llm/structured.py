import json
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

from app.llm.base import LLMInvalidOutput, LLMProvider

T = TypeVar("T", bound=BaseModel)
_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def _short(err: Exception) -> str:
    return str(err).replace("\n", " ")[:400]


def generate_structured(provider: LLMProvider, schema: type[T], messages: list[dict[str, str]], max_retries: int = 2) -> tuple[T, int]:
    """Ask for JSON, validate it against `schema`, and retry with the validation error up to `max_retries` times.
    Returns (model, retries_used). Raises LLMInvalidOutput when the model never produces valid output."""
    convo = list(messages)
    last: Exception | None = None
    for attempt in range(max_retries + 1):
        raw = provider.complete_json(convo)
        try:
            return schema.model_validate(json.loads(_FENCE.sub("", raw.strip()))), attempt
        except (json.JSONDecodeError, ValidationError) as e:
            last = e
            convo = [
                *messages,
                {"role": "assistant", "content": raw[:4000]},
                {"role": "user", "content": f"That was not valid. Problem: {_short(e)}. Return only the corrected JSON object."},
            ]
    raise LLMInvalidOutput(f"No valid output after {max_retries + 1} attempts: {_short(last) if last else ''}")
