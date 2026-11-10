"""The in-sandbox harness, exercised with TRUSTED fixture code only."""

import pytest

from tests.runner.helpers import case, run_harness

ADD = "def add(a, b):\n    return a + b\n"


def statuses(res):
    return [t["status"] for t in res["tests"]]


def test_pass_fail_and_actual_value():
    res = run_harness(ADD, "add", [case("t1", [1, 2], 3), case("t2", [1, 2], 4)])
    assert statuses(res) == ["passed", "failed"] and res["tests"][1]["actual"] == "3" and res["compile_error"] is None
    assert all(t["runtime_ms"] is not None for t in res["tests"]) and res["total_runtime_ms"] >= 0


def test_stdout_is_captured_and_capped_and_cannot_break_the_result():
    res = run_harness("def f():\n    print('hello')\n    print('x' * 200000)\n    return 1\n", "f", [case("t", [], 1)], output_kb=1)
    t = res["tests"][0]
    assert t["status"] == "passed" and t["stdout"].startswith("hello") and len(t["stdout"]) <= 2000


def test_exceptions_become_error_results_and_later_tests_still_run():
    code = "def f(x):\n    if x == 0:\n        raise ValueError('boom')\n    return x\n"
    res = run_harness(code, "f", [case("a", [0], 0), case("b", [5], 5)])
    assert statuses(res) == ["error", "passed"] and res["tests"][0]["error"] == "ValueError: boom"


def test_sys_exit_in_user_code_does_not_end_the_run():
    res = run_harness("import sys\ndef f(x):\n    if x == 1:\n        sys.exit(3)\n    return x\n", "f", [case("a", [1], 1), case("b", [2], 2)])
    assert statuses(res) == ["error", "passed"] and "SystemExit" in res["tests"][0]["error"]


def test_syntax_error_missing_function_and_top_level_failure():
    res = run_harness("def f(:\n    pass\n", "f", [case("t", [], 1)])
    assert res["compile_error"].startswith("SyntaxError") and statuses(res) == ["error"]
    res = run_harness("def other():\n    return 1\n", "f", [case("t", [], 1)])
    assert "MissingFunction" in res["compile_error"]
    res = run_harness("raise RuntimeError('at import')\n", "f", [case("t", [], 1)])
    assert "RuntimeError: at import" in res["compile_error"]


def test_slow_code_times_out_and_the_next_test_still_runs():
    code = "import time\ndef f(n):\n    if n:\n        while True:\n            pass\n    return 0\n"
    res = run_harness(code, "f", [case("slow", [1], 0), case("fast", [0], 0)], per_test_ms=300)
    assert statuses(res) == ["timeout", "passed"] and 250 <= res["tests"][0]["runtime_ms"] < 2000


def test_timeout_cannot_be_swallowed_by_except_exception():
    code = "def f():\n    while True:\n        try:\n            while True:\n                pass\n        except Exception:\n            pass\n"
    res = run_harness(code, "f", [case("t", [], 0)], per_test_ms=300)
    assert statuses(res) == ["timeout"]


def test_top_level_infinite_loop_is_stopped():
    res = run_harness("while True:\n    pass\n", "f", [case("t", [], 0)], per_test_ms=200)
    assert "Timeout" in res["compile_error"]


def test_non_json_return_values_are_errors():
    res = run_harness("def f():\n    return {1, 2}\n", "f", [case("t", [], [1, 2])])
    assert statuses(res) == ["error"] and "JSON" in res["tests"][0]["error"]


def test_tuples_match_lists_and_bools_are_not_numbers():
    res = run_harness("def f():\n    return (1, 2)\n", "f", [case("t", [], [1, 2])])
    assert statuses(res) == ["passed"]
    res = run_harness("def f():\n    return True\n", "f", [case("t", [], 1)])
    assert statuses(res) == ["failed"]
    res = run_harness("def f():\n    return 1\n", "f", [case("t", [], True)])
    assert statuses(res) == ["failed"]


def test_float_tolerance_applies_only_when_requested():
    code = "def f():\n    return 0.3333333333\n"
    assert statuses(run_harness(code, "f", [case("t", [], 0.333333, 1e-6)])) == ["passed"]
    assert statuses(run_harness(code, "f", [case("t", [], 0.333333)])) == ["failed"]
    assert statuses(run_harness("def f():\n    return [1, [2.0000001]]\n", "f", [case("t", [], [1, [2.0]], 1e-6)])) == ["passed"]


def test_each_test_gets_a_fresh_copy_of_its_arguments():
    code = "def f(xs):\n    xs.append(99)\n    return len(xs)\n"
    res = run_harness(code, "f", [case("a", [[1, 2]], 3), case("b", [[1, 2]], 3)])
    assert statuses(res) == ["passed", "passed"]


def test_recursion_error_is_reported_not_fatal():
    res = run_harness("def f(n):\n    return f(n + 1)\n", "f", [case("t", [0], 0)])
    assert statuses(res) == ["error"] and "Recursion" in res["tests"][0]["error"]


def test_long_values_and_errors_are_truncated():
    res = run_harness("def f():\n    return 'x' * 100000\n", "f", [case("t", [], "y")])
    assert len(res["tests"][0]["actual"]) <= 2000
    res = run_harness("def f():\n    raise ValueError('e' * 5000)\n", "f", [case("t", [], 1)])
    assert len(res["tests"][0]["error"]) <= 300


@pytest.mark.parametrize(
    "a,b,tol,ok",
    [
        (1, 1.0, None, True),
        ([1, 2], [1, 2, 3], None, False),
        ({"a": 1}, {"a": 1}, None, True),
        ({"a": 1}, {"b": 1}, None, False),
        ("x", "x", None, True),
        (None, None, None, True),
    ],
)
def test_equality_rules(a, b, tol, ok):
    import runner.harness as h

    assert h.equal(a, b, tol) is ok
