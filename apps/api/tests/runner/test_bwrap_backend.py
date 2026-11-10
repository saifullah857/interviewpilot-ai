"""The REAL sandbox backend (bubblewrap). Runs hostile and untrusted programs on purpose, but only inside the sandbox.
Skipped automatically where bubblewrap or unprivileged user namespaces are unavailable (for example plain Windows); run it inside WSL2 or Linux."""

import glob
import json
import os
import shutil
import subprocess
import tempfile
import threading
import time

import pytest
from fastapi.testclient import TestClient
from runner.app import create_app, sign
from runner.backends.bwrap import ENV_ALLOWED, BackendUnavailable, BwrapBackend
from runner.contract import RunnerRequest

from tests.runner.mutants import MUTANTS
from tests.runner.test_problem_bank import BY_SLUG, PROBLEMS, cases_of

PGREP = shutil.which("pgrep") or "/usr/bin/pgrep"
SANDBOX_DIRS = os.path.join(tempfile.gettempdir(), "ipr-*")  # the backend's per-run working folders


@pytest.fixture(scope="module")
def backend():
    try:
        b = BwrapBackend()
        b.self_check()
    except BackendUnavailable as e:
        pytest.skip(f"needs a working bubblewrap sandbox: {e}")
    return b


def make(code, tests, entry="f", **limits):
    return RunnerRequest.model_validate({"request_id": f"bw-{time.time_ns()}", "language": "python", "entry_point": entry, "code": code, "tests": tests, "limits": limits})


def one(code, expected=1, args=None, **limits):
    return make(code, [{"id": "t1", "args": args or [], "expected": expected}], **limits)


def run(backend, *a, **k):
    return backend.run(one(*a, **k))


# ------------------------------------------------------------------ the sandbox itself
def test_self_check_proves_every_isolation_property(backend):
    result = backend.self_check()
    assert len(result) == 9 and all(v is True for v in result.values()), result


# ------------------------------------------------------------------ ordinary behaviour
def test_correct_wrong_and_crashing_solutions(backend):
    ok = run(backend, "def f():\n    return 1\n")
    assert ok.executed and ok.backend == "bwrap" and ok.tests[0].status == "passed" and ok.tests[0].runtime_ms is not None
    assert run(backend, "def f():\n    return 2\n").tests[0].status == "failed"
    bad = run(backend, "def f():\n    return 1 / 0\n").tests[0]
    assert bad.status == "error" and "ZeroDivisionError" in bad.error
    assert run(backend, "def f():\n    raise SystemExit(3)\n").tests[0].status == "error"  # sys.exit() inside the function must not end the run


def test_comparison_rules_are_applied_outside_the_sandbox(backend):
    assert run(backend, "def f():\n    return 0.30000000000000004\n", expected=0.3).tests[0].status == "failed"
    r = backend.run(make("def f():\n    return 0.30000000000000004\n", [{"id": "t1", "args": [], "expected": 0.3, "tolerance": 1e-9}]))
    assert r.tests[0].status == "passed"
    assert run(backend, "def f():\n    return True\n", expected=1).tests[0].status == "failed"  # booleans are not numbers
    assert run(backend, "def f():\n    return (1, 2)\n", expected=[1, 2]).tests[0].status == "passed"  # tuples become lists
    assert run(backend, "def f():\n    return {1, 2}\n", expected=[1, 2]).tests[0].status == "error"  # not JSON-serialisable


def test_every_test_runs_in_a_fresh_sandbox_so_state_and_mutation_cannot_leak(backend):
    code = "calls = []\ndef f(xs):\n    xs.append(99)\n    calls.append(1)\n    return [len(xs), len(calls)]\n"
    r = backend.run(make(code, [{"id": f"t{i}", "args": [[1]], "expected": [2, 1]} for i in range(3)]))
    assert [t.status for t in r.tests] == ["passed"] * 3


def test_compile_errors_and_missing_functions_are_reported_not_hidden(backend):
    r = backend.run(make("def f(:\n", [{"id": "a", "args": [], "expected": 1}, {"id": "b", "args": [], "expected": 1}]))
    assert r.executed and r.compile_error.startswith("SyntaxError") and [t.status for t in r.tests] == ["error", "error"]
    assert "not_run" not in {t.status for t in r.tests}  # the API refuses an executing runner that leaves tests unrun
    m = run(backend, "def g():\n    return 1\n")
    assert m.compile_error and "MissingFunction" in m.compile_error


def test_a_reply_always_names_the_tests_that_were_sent_in_order(backend):
    ids = ["x1", "x2", "x3"]
    r = backend.run(make("def f(n):\n    return n\n", [{"id": i, "args": [k], "expected": k} for k, i in enumerate(ids)]))
    assert [t.id for t in r.tests] == ids and r.total_runtime_ms is not None


# ------------------------------------------------------------------ hostile programs
def test_infinite_loop_is_timed_out_quickly(backend):
    t0 = time.time()
    r = run(backend, "def f():\n    while True:\n        pass\n", per_test_ms=500)
    assert r.tests[0].status == "timeout" and time.time() - t0 < 6


def test_a_program_that_ignores_the_alarm_is_still_killed_from_outside(backend):
    t0 = time.time()
    r = run(backend, "import signal\nsignal.signal(signal.SIGALRM, signal.SIG_IGN)\ndef f():\n    while True:\n        pass\n", per_test_ms=500)
    assert r.tests[0].status == "timeout" and time.time() - t0 < 6


def test_a_single_huge_computation_that_never_returns_to_python_is_killed(backend):
    t0 = time.time()
    r = run(backend, "def f():\n    return len(str(10 ** 10 ** 8))\n", per_test_ms=500)
    assert r.tests[0].status in ("timeout", "error") and time.time() - t0 < 8


def test_total_wall_limit_stops_a_run_without_leaving_tests_unrun(backend):
    t0 = time.time()
    r = backend.run(make("def f():\n    while True:\n        pass\n", [{"id": f"t{i}", "args": [], "expected": 1} for i in range(10)], per_test_ms=500, total_wall_s=4))
    assert time.time() - t0 < 9 and len(r.tests) == 10
    assert {t.status for t in r.tests} == {"timeout"} and any("total time limit" in (t.error or "") for t in r.tests)


def test_memory_bomb_is_refused_not_survived_by_the_host(backend):
    r = run(backend, "def f():\n    return len(bytearray(2 * 1024 ** 3))\n", memory_mb=64)
    assert r.tests[0].status == "error" and "Memory" in (r.tests[0].error or "")


def test_fork_bomb_and_process_spawning_are_contained(backend):
    before = subprocess.run([PGREP, "-c", "-f", "python3 -I -S -B"], capture_output=True, text=True).stdout.strip()  # noqa: S603 - fixed arguments, no user input
    r = run(backend, "import os\ndef f():\n    for _ in range(500):\n        os.fork()\n    return 1\n", per_test_ms=1000)
    assert r.tests[0].status in ("error", "timeout")
    s = run(backend, "import subprocess\ndef f():\n    subprocess.run(['/usr/bin/sleep', '60'])\n    return 1\n", per_test_ms=1000)
    assert s.tests[0].status in ("error", "timeout")
    time.sleep(0.5)
    after = subprocess.run([PGREP, "-c", "-f", "python3 -I -S -B"], capture_output=True, text=True).stdout.strip()  # noqa: S603 - fixed arguments, no user input
    assert before == after, "sandbox processes were left behind"
    assert not subprocess.run([PGREP, "-f", "sleep 60"], capture_output=True, text=True).stdout.strip()  # noqa: S603 - fixed arguments, no user input


def test_a_fork_bomb_is_capped_at_a_handful_of_processes(backend):
    code = "import os, time\ndef f():\n    n = 0\n    try:\n        for _ in range(300):\n            if os.fork() == 0:\n                time.sleep(5)\n                os._exit(0)\n            n += 1\n    except OSError:\n        pass\n    return n\n"
    r = run(backend, code, expected=-1, per_test_ms=2000)
    assert r.tests[0].status == "failed" and int(r.tests[0].actual) <= 16, r.tests[0]  # at most the process limit, never hundreds
    time.sleep(0.3)
    assert not subprocess.run([PGREP, "-f", "python3 -I -S -B"], capture_output=True, text=True).stdout.strip()  # noqa: S603 - fixed arguments, no user input


def test_the_runner_refuses_to_run_as_root(monkeypatch):
    monkeypatch.setattr(os, "geteuid", lambda: 0)
    with pytest.raises(BackendUnavailable) as e:
        BwrapBackend()
    assert "root" in str(e.value) and "fork bomb" in str(e.value)


def test_network_is_blocked(backend):
    r = run(backend, "import socket\ndef f():\n    socket.create_connection(('1.1.1.1', 53), timeout=2)\n    return 1\n")
    assert r.tests[0].status == "error"
    d = run(backend, "import socket\ndef f():\n    socket.getaddrinfo('example.com', 80)\n    return 1\n")
    assert d.tests[0].status == "error"


def test_the_filesystem_is_read_only_private_and_empty_of_host_files(backend):
    assert run(backend, "def f():\n    open('/usr/local/evil.txt', 'w').write('x')\n    return 1\n").tests[0].status == "error"
    seen = run(backend, "import os\ndef f():\n    return [p for p in ('/home', '/root', '/etc/passwd', '/mnt', '/var', '/opt') if os.path.exists(p)]\n", expected=[])
    assert seen.tests[0].status == "passed"
    big = run(backend, "def f():\n    open('/tmp/x', 'wb').write(b'x' * (20 * 1024 * 1024))\n    return 1\n")
    assert big.tests[0].status == "error"  # file-size limit


def test_the_runners_environment_and_secrets_never_reach_the_sandbox(backend, monkeypatch):
    monkeypatch.setenv("RUNNER_SHARED_SECRET", "S" * 40)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_" + "k" * 30)
    r = run(backend, "import os\ndef f():\n    return sorted(os.environ)\n", expected=[])
    keys = set(json.loads(r.tests[0].actual))
    assert keys <= ENV_ALLOWED and not any(k in keys for k in ("RUNNER_SHARED_SECRET", "GROQ_API_KEY", "DATABASE_URL"))


def test_a_large_correct_answer_is_checked_and_an_absurd_one_is_refused(backend):
    big = [[i, i + 1] for i in range(9000)]  # about 90,000 characters of JSON: larger than any answer in the bank
    ok = backend.run(make("def f():\n    return [[i, i + 1] for i in range(9000)]\n", [{"id": "t1", "args": [], "expected": big}], per_test_ms=2000))
    assert ok.tests[0].status == "passed"
    wrong = backend.run(make("def f():\n    return [[i, i + 2] for i in range(9000)]\n", [{"id": "t1", "args": [], "expected": big}], per_test_ms=2000))
    assert wrong.tests[0].status == "failed" and len(wrong.tests[0].actual) <= 2000
    huge = run(backend, "def f():\n    return 'x' * 400000\n", per_test_ms=2000)
    assert huge.tests[0].status == "error" and "too large" in huge.tests[0].error


def test_endless_output_is_capped_and_cannot_flood_the_reply(backend):
    r = run(backend, "def f():\n    for _ in range(100000):\n        print('x' * 1000)\n    return 1\n", per_test_ms=2000)
    t = r.tests[0]
    assert t.stdout is None or len(t.stdout) <= 2000
    assert len(r.model_dump_json()) < 20_000


def test_exiting_the_interpreter_is_an_error_not_a_pass(backend):
    r = run(backend, "import os\ndef f():\n    os._exit(0)\n")
    assert r.tests[0].status == "error" and "without reporting" in r.tests[0].error


def test_deep_recursion_is_an_error(backend):
    assert run(backend, "def f():\n    return f()\n").tests[0].status == "error"


# ------------------------------------------------------------------ hidden answers and forged results
def test_expected_answers_never_enter_the_sandbox(backend):
    secret = "SENTINEL-EXPECTED-9731"
    r = run(backend, "def f():\n    return open('/work/request.json').read()\n", expected=secret)
    shown = r.tests[0].actual
    seen_inside = json.loads(json.loads(shown))  # what the sandbox could read: the request file, as the program saw it
    assert r.tests[0].status == "failed" and secret not in shown
    assert seen_inside["tests"] == [{"id": "t1", "args": []}], seen_inside  # arguments only: no expected answer, no tolerance


def test_a_reported_pass_is_never_accepted_from_inside_the_sandbox(backend):
    forged = 'import os\ndef f():\n    os.write(1, b\'{"tests":[{"id":"t1","status":"passed","actual_full":"1"}]}\\n\')\n    os._exit(0)\n'
    assert run(backend, forged, expected=424242).tests[0].status != "passed"
    guessed = 'import os\ndef f():\n    os.write(1, b\'{"tests":[{"id":"t1","status":"ran","actual_full":"1"}]}\\n\')\n    os._exit(0)\n'
    assert run(backend, guessed, expected=424242).tests[0].status == "failed"  # a forged answer still has to equal the real one, which it cannot know


def test_oversized_or_malformed_forged_replies_are_bounded(backend):
    flood = "import os\ndef f():\n    while True:\n        os.write(1, b'x' * 65536)\n"
    t0 = time.time()
    r = run(backend, flood, per_test_ms=500)
    assert r.tests[0].status in ("timeout", "error") and time.time() - t0 < 8 and len(r.model_dump_json()) < 20_000


# ------------------------------------------------------------------ the service stays responsive during a run
def test_health_answers_while_a_slow_run_is_in_progress(backend):
    secret = "s" * 40
    client = TestClient(create_app(secret, backend))
    raw = json.dumps({"request_id": "slowrun-0001", "language": "python", "entry_point": "f", "code": "def f():\n    while True:\n        pass\n", "tests": [{"id": "t1", "args": [], "expected": 1}], "limits": {"per_test_ms": 1000, "total_wall_s": 6}}).encode()
    ts = int(time.time())
    out = {}

    def call():
        out["r"] = client.post("/execute", content=raw, headers={"X-Runner-Timestamp": str(ts), "X-Runner-Signature": sign(secret, ts, raw), "Content-Type": "application/json"})

    th = threading.Thread(target=call)
    th.start()
    time.sleep(1.0)
    t0 = time.time()
    h = client.get("/health")
    assert h.status_code == 200 and h.json()["executes_code"] is True and time.time() - t0 < 1.5, "the event loop was blocked by a run"
    th.join(timeout=30)
    assert out["r"].status_code == 200 and out["r"].json()["tests"][0]["status"] == "timeout"


def test_no_temp_folders_are_left_behind(backend):
    before = set(glob.glob(SANDBOX_DIRS))
    run(backend, "def f():\n    return 1\n")
    run(backend, "def f():\n    while True:\n        pass\n", per_test_ms=300)
    assert set(glob.glob(SANDBOX_DIRS)) == before


def test_the_service_refuses_to_start_when_the_sandbox_is_unsafe(monkeypatch):
    from runner import app as runner_app

    monkeypatch.setenv("RUNNER_BACKEND", "bwrap")
    monkeypatch.setenv("RUNNER_SHARED_SECRET", "s" * 40)
    monkeypatch.setenv("RUNNER_BWRAP", "/nonexistent/bwrap")
    monkeypatch.setattr(os, "geteuid", lambda: 1000)  # behave as a normal user so the missing-bubblewrap path is what is tested
    with pytest.raises(SystemExit) as e:
        runner_app.app_from_env()
    assert "Refusing to start" in str(e.value) and "bubblewrap" in str(e.value)
    monkeypatch.setenv("RUNNER_BACKEND", "docker")
    with pytest.raises(SystemExit):
        runner_app.app_from_env()


# ------------------------------------------------------------------ the whole problem bank, under REAL execution
@pytest.mark.parametrize("slug", [p["slug"] for p in PROBLEMS])
def test_reference_solution_passes_every_test_under_real_execution(backend, slug):
    p = BY_SLUG[slug]
    r = backend.run(make(p["reference_solution"], cases_of(p), entry=p["entry_point"], per_test_ms=p["per_test_ms"]))
    bad = [(t.id, t.status, t.error) for t in r.tests if t.status != "passed"]
    assert r.executed and not bad, bad
    assert max(t.runtime_ms for t in r.tests) < p["per_test_ms"] / 2  # real timings, with headroom


@pytest.mark.parametrize("slug", [p["slug"] for p in PROBLEMS])
def test_starter_code_fails_under_real_execution(backend, slug):
    p = BY_SLUG[slug]
    r = backend.run(make(p["starter_code"], cases_of(p), entry=p["entry_point"], per_test_ms=p["per_test_ms"]))
    assert all(t.status == "failed" for t in r.tests), slug


def _mutants():
    return [(slug, m["name"]) for slug, ms in MUTANTS.items() for m in ms]


@pytest.mark.parametrize("slug,name", _mutants())
def test_wrong_solutions_are_caught_by_the_hidden_tests_under_real_execution(backend, slug, name):
    p = BY_SLUG[slug]
    m = next(x for x in MUTANTS[slug] if x["name"] == name)
    limit = 1000 if m.get("slow") else p["per_test_ms"]
    r = backend.run(make(m["code"], cases_of(p), entry=p["entry_point"], per_test_ms=limit, total_wall_s=30))
    hidden = {t["id"] for t in p["hidden_tests"]}
    assert any(t.status != "passed" for t in r.tests if t.id in hidden), f"{slug}: '{name}' passes every hidden test"
    if m.get("slow"):
        assert "timeout" in {t.status for t in r.tests}
