"""The LOCAL process backend (works on Windows without WSL). Runs real programs, including hostile-ish ones, in child processes.
It is a practice-on-your-own-machine backend, not a security boundary; these tests check it does the job and stops the obvious misuse."""

import time

import pytest
from runner.backends.local import LocalBackend
from runner.contract import RunnerRequest

from tests.runner.test_problem_bank import PROBLEMS, cases_of

b = LocalBackend()


def go(code, tests, per=1000, entry="solve"):
    req = RunnerRequest(request_id="abcdefgh12", language="python", entry_point=entry, code=code,
                        tests=[{"id": f"t{i}", "args": a, "expected": e} for i, (a, e) in enumerate(tests)], limits={"per_test_ms": per, "total_wall_s": 30})
    return b.run(req)


def statuses(r):
    return [t.status for t in r.tests]


def test_self_check_passes():
    assert b.self_check()["simple_function"]


def test_correct_wrong_and_syntax_error():
    assert statuses(go("def solve(a, b):\n    return a + b", [([1, 2], 3), ([5, 5], 10)])) == ["passed", "passed"]
    assert statuses(go("def solve(a, b):\n    return a - b", [([1, 2], 3)])) == ["failed"]
    r = go("def solve(a, b)\n    return a", [([1, 2], 3)])
    assert r.compile_error and statuses(r) == ["error"]


def test_infinite_loop_is_stopped_quickly():
    t = time.time()
    r = go("def solve(a, b):\n    while True:\n        pass", [([1, 2], 3)], per=400)
    assert statuses(r) == ["timeout"] and time.time() - t < 12


@pytest.mark.parametrize("code", [
    "import os\ndef solve(a, b):\n    return os.getcwd()",
    "import subprocess\ndef solve(a, b):\n    return 1",
    "import socket\ndef solve(a, b):\n    return 1",
    "def solve(a, b):\n    return open('/etc/passwd').read()",
    "def solve(a, b):\n    return eval('1+1')",
])
def test_dangerous_things_are_refused_and_never_pass(code):
    assert statuses(go(code, [([1, 2], 2)])) == ["error"]


def test_safe_imports_work_and_output_is_captured():
    r = go("import math, heapq\nfrom collections import Counter\ndef solve(a, b):\n    print('hi')\n    return math.gcd(a, b)", [([4, 6], 2)])
    assert statuses(r) == ["passed"] and r.tests[0].stdout.strip() == "hi"


def test_memory_hog_does_not_pass():
    assert statuses(go("def solve(a, b):\n    x = [0] * (10 ** 10)\n    return 1", [([1, 2], 1)], per=1500))[0] in ("error", "timeout")


def test_the_child_never_receives_the_expected_answer_or_secrets(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "gsk_super_secret")
    r = go("def solve(a, b):\n    return 3", [([1, 2], 3)])
    assert statuses(r) == ["passed"]
    from runner.backends.local import _minimal_env

    assert "GROQ_API_KEY" not in _minimal_env()


@pytest.mark.parametrize("slug", ["two-sum", "binary-search", "min-max-scale"])
def test_reference_solutions_pass_every_hidden_test(slug):
    p = next(x for x in PROBLEMS if x["slug"] == slug)
    req = RunnerRequest(request_id="abcdefgh12", language="python", entry_point=p["entry_point"], code=p["reference_solution"], tests=cases_of(p), limits={"per_test_ms": p["per_test_ms"], "total_wall_s": 30})
    r = b.run(req)
    assert all(t.status == "passed" for t in r.tests), [t.model_dump() for t in r.tests if t.status != "passed"]
