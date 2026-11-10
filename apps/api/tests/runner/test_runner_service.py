import json
import os
import time

from fastapi.testclient import TestClient
from runner.app import MAX_BODY, create_app, sign
from runner.backends.mock import MockBackend
from runner.contract import CONTRACT_VERSION

SECRET = "s" * 40


def make_client():
    return TestClient(create_app(SECRET, MockBackend()))


def body(**over):
    req = {
        "request_id": "req-12345678",
        "language": "python",
        "entry_point": "add",
        "code": "def add(a, b):\n    return a + b\n",
        "tests": [{"id": "t1", "args": [1, 2], "expected": 3}, {"id": "t2", "args": [2, 2], "expected": 4}],
        "limits": {},
    }
    req.update(over)
    return json.dumps(req).encode()


def post(client, raw, secret=SECRET, ts=None, sig=None, **headers):
    ts = int(time.time()) if ts is None else ts
    h = {"X-Runner-Timestamp": str(ts), "X-Runner-Signature": sig if sig is not None else sign(secret, ts, raw), "Content-Type": "application/json", **headers}
    return client.post("/execute", content=raw, headers=h)


def test_health_says_the_mock_executes_nothing():
    r = make_client().get("/health")
    assert r.json() == {"status": "ok", "backend": "mock", "version": "1", "executes_code": False, "contract": CONTRACT_VERSION}


def test_mock_never_executes_code_and_never_reports_a_pass(tmp_path):
    marker = tmp_path / "executed.txt"
    code = f"open({str(marker)!r}, 'w').write('ran')\ndef add(a, b):\n    return a + b\n"
    r = post(make_client(), body(code=code))
    assert r.status_code == 200
    data = r.json()
    assert data["executed"] is False and data["backend"] == "mock" and data["request_id"] == "req-12345678"
    assert [t["status"] for t in data["tests"]] == ["not_run", "not_run"] and [t["id"] for t in data["tests"]] == ["t1", "t2"]
    assert all(t["actual"] is None and t["runtime_ms"] is None for t in data["tests"]) and not marker.exists()


def test_unsigned_wrongly_signed_and_tampered_requests_are_rejected():
    c = make_client()
    raw = body()
    assert c.post("/execute", content=raw).status_code == 401
    assert post(c, raw, secret="x" * 40).json()["error"]["code"] == "bad_signature"
    ts = int(time.time())
    good = sign(SECRET, ts, raw)
    assert post(c, body(code="def add(a, b):\n    return 0\n"), ts=ts, sig=good).json()["error"]["code"] == "bad_signature"  # body changed after signing
    assert post(c, raw, ts=ts + 1, sig=good).json()["error"]["code"] == "bad_signature"  # timestamp changed after signing
    assert c.post("/execute", content=raw, headers={"X-Runner-Timestamp": "abc", "X-Runner-Signature": "x"}).status_code == 401


def test_old_and_future_timestamps_and_replays_are_rejected():
    c = make_client()
    raw = body()
    assert post(c, raw, ts=int(time.time()) - 600).json()["error"]["code"] == "stale"
    assert post(c, raw, ts=int(time.time()) + 600).json()["error"]["code"] == "stale"
    ts = int(time.time())
    sig = sign(SECRET, ts, raw)
    assert post(c, raw, ts=ts, sig=sig).status_code == 200
    again = post(c, raw, ts=ts, sig=sig)
    assert again.status_code == 401 and again.json()["error"]["code"] == "replay"


def test_oversized_and_malformed_requests_are_rejected():
    c = make_client()
    assert post(c, b"x" * (MAX_BODY + 10)).status_code == 413
    assert post(c, b"not json").json()["error"]["code"] == "invalid_request"
    for bad in (
        body(language="javascript"),
        body(entry_point="__import__('os')"),
        body(tests=[]),
        body(code=""),
        body(request_id="x"),
        body(limits={"per_test_ms": 10**9}),
        body(extra=1),
    ):
        assert post(c, bad).status_code == 400, bad[:80]
    too_many = [{"id": f"t{i}", "args": [], "expected": 1} for i in range(61)]
    assert post(c, body(tests=too_many)).status_code == 400


def test_the_service_refuses_to_start_with_a_weak_secret_or_an_unavailable_backend(monkeypatch):
    import pytest

    with pytest.raises(ValueError):
        create_app("short", MockBackend())
    from runner.app import app_from_env

    monkeypatch.setenv("RUNNER_SHARED_SECRET", SECRET)
    monkeypatch.setenv("RUNNER_BACKEND", "docker")
    with pytest.raises(SystemExit):
        app_from_env()
    monkeypatch.setenv("RUNNER_BACKEND", "mock")
    assert app_from_env().title.startswith("InterviewPilot")


def test_the_runner_package_never_imports_the_api_or_its_secrets():
    import pathlib
    import re

    src = "\n".join(p.read_text() for p in pathlib.Path(__file__).resolve().parents[4].joinpath("services", "sandbox-runner", "runner").rglob("*.py"))
    assert not re.search(r"^\s*(from|import)\s+app(\.|\s|$)", src, re.M)  # no imports from the API package
    assert "DATABASE_URL" not in src and "SECRET_KEY" not in src and os.environ["SECRET_KEY"] not in src
