"""How the API talks to a code runner. The API never runs submitted code: it only sends it to a runner and trusts nothing
about the reply until validate_response() has checked it against what was asked."""

import hashlib
import hmac
import json
import sys
import time
import uuid
from pathlib import Path

import httpx

from app.coding.runner_contract import CaseResult, RunnerRequest, RunnerResponse
from app.core.config import get_settings


class RunnerUnavailable(Exception):
    """The runner could not be reached or refused the request. Messages never contain secrets or code."""


class RunnerBadResponse(Exception):
    """The runner answered, but not in a way we can trust."""


def sign(secret: str, timestamp: int, body: bytes) -> str:
    return hmac.new(secret.encode(), f"{timestamp}.".encode() + body, hashlib.sha256).hexdigest()


def new_request_id() -> str:
    return uuid.uuid4().hex


def validate_response(req: RunnerRequest, resp: RunnerResponse) -> None:
    """The reply must describe exactly the tests we sent, in order, and be internally consistent."""
    if resp.request_id != req.request_id:
        raise RunnerBadResponse("request id mismatch")
    if [t.id for t in resp.tests] != [t.id for t in req.tests]:
        raise RunnerBadResponse("the tests in the reply do not match the tests sent")
    statuses = {t.status for t in resp.tests}
    if not resp.executed and statuses != {"not_run"}:
        raise RunnerBadResponse("a runner that did not execute code reported results")
    if resp.executed and "not_run" in statuses and resp.compile_error is None:
        raise RunnerBadResponse("an executing runner left tests unrun without a reason")


class MockRunnerClient:
    """DEVELOPMENT MOCK, in-process. Executes nothing and never reports a pass."""

    mode = "mock"

    def run(self, req: RunnerRequest) -> RunnerResponse:
        return RunnerResponse(
            request_id=req.request_id,
            backend="mock",
            backend_version="1",
            executed=False,
            compile_error=None,
            tests=[CaseResult(id=t.id, status="not_run") for t in req.tests],
            total_runtime_ms=None,
        )

    def status(self) -> dict:
        return {
            "mode": "mock",
            "executes_code": False,
            "reachable": True,
            "backend": "mock",
            "message": "The code runner is switched off (RUNNER_MODE=mock), so code is NOT run. Close everything and start the app with START.bat: it turns the runner on for you.",
        }


class HttpRunnerClient:
    mode = "http"

    def __init__(self, url: str, secret: str, timeout: int):
        self.url, self.secret, self.timeout = url.rstrip("/"), secret, timeout

    def run(self, req: RunnerRequest) -> RunnerResponse:
        body = req.model_dump_json().encode()
        ts = int(time.time())
        headers = {"X-Runner-Timestamp": str(ts), "X-Runner-Signature": sign(self.secret, ts, body), "Content-Type": "application/json"}
        try:
            r = httpx.post(f"{self.url}/execute", content=body, headers=headers, timeout=self.timeout)
        except httpx.HTTPError as e:
            raise RunnerUnavailable("Could not reach the code runner.") from e
        if r.status_code != 200:
            raise RunnerUnavailable(f"The code runner refused the request ({r.status_code}).")
        try:
            resp = RunnerResponse.model_validate(r.json())
        except ValueError as e:
            raise RunnerBadResponse("malformed reply") from e
        validate_response(req, resp)
        return resp

    def status(self) -> dict:
        try:
            r = httpx.get(f"{self.url}/health", timeout=3)
            d = r.json()
            return {
                "mode": "http",
                "executes_code": bool(d.get("executes_code")),
                "reachable": r.status_code == 200,
                "backend": str(d.get("backend", "unknown")),
                "message": f"Connected to the code runner ({d.get('backend', '?')})." if d.get("executes_code") else "The runner is a development mock: submitted code is NOT run.",
            }
        except (httpx.HTTPError, ValueError):
            return {"mode": "http", "executes_code": False, "reachable": False, "backend": "unknown", "message": "The code runner cannot be reached. Start the app with START.bat (it opens a Runner window), or run scripts\\run_runner.py."}


class LocalRunnerClient:
    """Runs submitted code on THIS computer through the sandbox-runner's LOCAL backend, inside the API process.
    No second window and no shared secret are needed, so submitting code works the moment the API starts.
    Submitted code is still never executed inside the API process: the runner service's local backend starts a fresh child Python
    process per test, with the restrictions described in services/sandbox-runner/runner/backends/local.py. Meant for one person on their own machine."""

    mode = "local"
    _backend = None
    _error: str | None = None

    @classmethod
    def _load(cls):
        if cls._backend is not None or cls._error is not None:
            return cls._backend
        try:
            root = Path(__file__).resolve().parents[4] / "services" / "sandbox-runner"
            if str(root) not in sys.path:
                sys.path.insert(0, str(root))
            from runner.backends.local import LocalBackend

            errors = []
            for python in LocalBackend.candidates():
                backend = LocalBackend(python=python)
                try:
                    backend.self_check()
                except Exception as e:  # noqa: BLE001 - try the next interpreter
                    errors.append(f"{e}")
                    continue
                cls._backend = backend
                break
            if cls._backend is None:
                raise RuntimeError(" | ".join(errors) or "no Python interpreter found")
        except Exception as e:  # noqa: BLE001 - any failure means "cannot execute"; reported honestly below
            cls._error = f"{type(e).__name__}: {e}"[:400]
        return cls._backend

    def run(self, req: RunnerRequest) -> RunnerResponse:
        backend = self._load()
        if backend is None:
            raise RunnerUnavailable("The local code runner could not start.")
        from runner.contract import RunnerRequest as RunnerReq  # the runner package's own copy of the contract

        try:
            raw = backend.run(RunnerReq.model_validate(req.model_dump()))
            resp = RunnerResponse.model_validate(raw.model_dump(mode="json"))
        except Exception as e:  # noqa: BLE001
            raise RunnerBadResponse("local runner failure") from e
        validate_response(req, resp)
        return resp

    def status(self) -> dict:
        ok = self._load() is not None
        return {
            "mode": "local",
            "executes_code": ok,
            "reachable": ok,
            "backend": "local" if ok else "unavailable",
            "message": "Your code is run on this computer by the built-in code runner." if ok else f"The built-in code runner could not start ({self._error}). Check that Python is installed.",
        }


def get_runner():
    """FastAPI dependency; tests override it."""
    s = get_settings()
    if s.runner_mode == "http":
        return HttpRunnerClient(s.runner_url, s.runner_shared_secret, s.runner_timeout_seconds)
    if s.runner_mode == "local":
        return LocalRunnerClient()
    return MockRunnerClient()


__all__ = ["HttpRunnerClient", "LocalRunnerClient", "MockRunnerClient", "RunnerBadResponse", "RunnerUnavailable", "get_runner", "json"]
