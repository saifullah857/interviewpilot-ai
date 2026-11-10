
import logging
import time

import httpx

from app.llm.base import (
    LLMNotConfigured,
    LLMRateLimited,
    LLMUnavailable,
)

log = logging.getLogger("interviewpilot")

_sleep = time.sleep
MAX_WAIT_S = 20


class GroqProvider:
    """Groq OpenAI-compatible chat completion provider."""

    name = "groq"

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        timeout: int,
        *,
        max_tokens: int = 4096,
        reasoning_effort: str = "low",
        fallback_model: str = "",
        retries: int = 2,
    ):
        if not api_key or not model:
            raise LLMNotConfigured(
                "GROQ_API_KEY and LLM_MODEL_PRIMARY must both be set."
            )

        self._key = api_key
        self.model = model
        self._url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_tokens = max_tokens
        self._effort = reasoning_effort
        self._fallback = (
            fallback_model
            if fallback_model and fallback_model != model
            else ""
        )
        self._retries = max(0, retries)

    def _body(
        self,
        model: str,
        messages: list[dict[str, str]],
    ) -> dict:
        body = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Return valid JSON only. "
                        "Return one JSON object without Markdown."
                    ),
                },
                *messages,
            ],
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }

        if self._max_tokens:
            body["max_completion_tokens"] = self._max_tokens

        if self._effort and "gpt-oss" in model.lower():
            body["reasoning_effort"] = self._effort

        return body

    def _once(
        self,
        model: str,
        messages: list[dict[str, str]],
    ) -> str:
        try:
            response = httpx.post(
                f"{self._url}/chat/completions",
                json=self._body(model, messages),
                headers={
                    "Authorization": f"Bearer {self._key}",
                    "Content-Type": "application/json",
                },
                timeout=self._timeout,
            )

        except httpx.TimeoutException as e:
            log.warning(
                "Groq timeout (%s) on %s",
                type(e).__name__,
                model,
            )
            raise LLMUnavailable(
                "The AI provider request timed out."
            ) from e

        except httpx.HTTPError as e:
            log.warning(
                "Groq connection error (%s) on %s",
                type(e).__name__,
                model,
            )
            raise LLMUnavailable(
                "Could not reach the AI provider."
            ) from e

        code = response.status_code

        if code == 429:
            retry_after = response.headers.get("retry-after")

            log.warning(
                "Groq rate limit on %s (retry-after=%s)",
                model,
                retry_after,
            )

            try:
                retry_seconds = (
                    int(float(retry_after))
                    if retry_after
                    else None
                )
            except (ValueError, TypeError):
                retry_seconds = None

            raise LLMRateLimited(retry_seconds)

        if code in (400, 401, 403, 404):
            # Diagnostic detail: provider error only, truncated.
            # Do not log request headers or API keys.
            error_detail = response.text[:1000]

            log.error(
                "Groq HTTP %s on model %s. Provider detail: %s",
                code,
                model,
                error_detail,
            )

            if code in (401, 403):
                raise LLMUnavailable(
                    "The AI provider rejected the API key."
                )

            raise LLMUnavailable(
                f"The AI provider returned an error ({code})."
            )

        if code >= 500:
            log.warning(
                "Groq server error HTTP %s on %s",
                code,
                model,
            )
            raise LLMUnavailable(
                f"The AI provider returned a server error ({code})."
            )

        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            if not isinstance(content, str) or not content.strip():
                raise ValueError("Empty response")

            return content

        except (KeyError, IndexError, ValueError, TypeError) as e:
            log.error(
                "Unexpected Groq response format on %s",
                model,
            )
            raise LLMUnavailable(
                "The AI provider returned an unexpected response."
            ) from e

    def _with_retries(
        self,
        model: str,
        messages: list[dict[str, str]],
    ) -> str:
        last = None

        for attempt in range(self._retries + 1):
            try:
                return self._once(model, messages)

            except LLMRateLimited as e:
                last = e
                wait = (
                    e.retry_after
                    if e.retry_after is not None
                    else 3 * (attempt + 1)
                )

                if attempt >= self._retries or wait > MAX_WAIT_S:
                    break

                _sleep(max(1, wait))

            except LLMUnavailable as e:
                last = e

                # Invalid request, invalid model or credentials:
                # retrying the same request will not fix these.
                if any(
                    marker in str(e)
                    for marker in (
                        "rejected the API key",
                        "returned an error (400)",
                        "returned an error (401)",
                        "returned an error (403)",
                        "returned an error (404)",
                        "unexpected response",
                    )
                ):
                    break

                if attempt >= self._retries:
                    break

                _sleep(1.5 * (attempt + 1))

        if last is not None:
            raise last

        raise LLMUnavailable("The AI provider request failed.")

    def complete_json(
        self,
        messages: list[dict[str, str]],
    ) -> str:
        try:
            return self._with_retries(self.model, messages)

        except (LLMRateLimited, LLMUnavailable) as primary_error:
            if (
                not self._fallback
                or "rejected the API key" in str(primary_error)
            ):
                raise

            log.warning(
                "Primary model %s failed; trying fallback %s",
                self.model,
                self._fallback,
            )

            try:
                return self._with_retries(
                    self._fallback,
                    messages,
                )

            except (LLMRateLimited, LLMUnavailable) as fallback_error:
                log.error(
                    "Both Groq models failed. Primary: %s | Fallback: %s",
                    primary_error,
                    fallback_error,
                )
                raise fallback_error from primary_error
