"""CONFORMANCE SUITE FOR A REAL ISOLATED BACKEND. Skipped unless RUNNER_CONFORMANCE_URL and RUNNER_SHARED_SECRET are set.

WARNING: these are hostile programs. Run this ONLY against a runner whose backend is a genuine sandbox (see docs/SANDBOX_DESIGN.md).
Never point it at the mock (it would pass trivially) or at anything that executes code on a machine you care about.
Phase 7 cannot be called complete until this suite passes against the approved backend."""

import json
import os
import time

import httpx
import pytest

URL, SECRET = os.environ.get("RUNNER_CONFORMANCE_URL", ""), os.environ.get("RUNNER_SHARED_SECRET", "")
pytestmark = pytest.mark.skipif(not (URL and SECRET), reason="needs a real isolated runner: set RUNNER_CONFORMANCE_URL and RUNNER_SHARED_SECRET")

HOSTILE = {
    "infinite_loop": ("def f():\n    while True:\n        pass\n", {"timeout", "error"}),
    "ignore_alarm_signal": ("import signal\nsignal.signal(signal.SIGALRM, signal.SIG_IGN)\ndef f():\n    while True:\n        pass\n", {"timeout", "error"}),
    "memory_bomb": ("def f():\n    return len(bytearray(8 * 1024 ** 3))\n", {"error", "timeout"}),
    "fork_bomb_attempt": ("import os\ndef f():\n    for _ in range(2000):\n        os.fork()\n    return 1\n", {"error", "timeout"}),
    "network_access": ("import socket\ndef f():\n    socket.create_connection(('example.com', 80), timeout=3)\n    return 1\n", {"error", "timeout"}),
    "write_outside_workdir": ("def f():\n    open('/usr/local/evil.txt', 'w').write('x')\n    return 1\n", {"error"}),
    "spawn_process": ("import subprocess\ndef f():\n    subprocess.run(['sleep', '100'])\n    return 1\n", {"error", "timeout"}),
    "exit_the_interpreter": ("import os\ndef f():\n    os._exit(0)\n", {"error"}),
    "endless_output": ("def f():\n    while True:\n        print('x' * 1000)\n", {"timeout", "error"}),
    "deep_recursion": ("def f():\n    return f()\n", {"error"}),
    "read_runner_secret": ("import os\ndef f():\n    return dict(os.environ)\n", {"passed", "failed", "error"}),
}


def call(code: str) -> dict:
    from runner.app import sign

    raw = json.dumps(
        {
            "request_id": f"conf-{time.time_ns()}",
            "language": "python",
            "entry_point": "f",
            "code": code,
            "tests": [{"id": "t1", "args": [], "expected": 1}],
            "limits": {"per_test_ms": 1000, "total_wall_s": 10, "memory_mb": 128},
        }
    ).encode()
    ts = int(time.time())
    r = httpx.post(
        f"{URL}/execute",
        content=raw,
        headers={"X-Runner-Timestamp": str(ts), "X-Runner-Signature": sign(SECRET, ts, raw), "Content-Type": "application/json"},
        timeout=60,
    )
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize("name", sorted(HOSTILE))
def test_hostile_program_is_contained(name):
    code, allowed = HOSTILE[name]
    start = time.time()
    data = call(code)
    assert time.time() - start < 40, "the runner must enforce its wall-clock limit"
    assert data["executed"] is True and data["tests"][0]["status"] in allowed, data
    assert len(json.dumps(data)) < 20_000  # output is bounded
    assert httpx.get(f"{URL}/health", timeout=10).json()["status"] == "ok"  # the runner is still healthy afterwards
    if name == "read_runner_secret":
        assert SECRET not in json.dumps(data), "the runner's secret leaked into the sandbox"


def test_a_correct_solution_still_passes_after_all_that():
    data = call("def f():\n    return 1\n")
    assert data["tests"][0]["status"] == "passed"
