"""Runs ONE submission against its test cases. This is the program a real, isolated backend executes INSIDE its sandbox
(container or similar): `python harness.py request.json result.json`. It uses only the standard library.

It is NOT a sandbox. It trusts nothing it is given but it cannot stop code from reading files, opening sockets or using
memory: those limits must come from the backend that launches it. Never run it on untrusted code outside such a sandbox."""
import contextlib
import copy
import io
import json
import os
import signal
import sys
import time

try:
    import resource  # POSIX only; the real sandbox backend is Linux
except ImportError:  # pragma: no cover
    resource = None

MAX_ACTUAL = 2000
MAX_ERROR = 300
MAX_FULL = 150_000  # sandbox mode: the whole returned value goes back for comparison outside. The largest legitimate answer in the problem bank is about 69,000 characters


class _Timeout(BaseException):  # BaseException so `except Exception` in user code cannot swallow it
    pass


# Local (no-WSL) mode: best-effort restrictions on top of the process limits set by the parent. NOT a security boundary.
SAFE_IMPORTS = {
    "math", "cmath", "collections", "heapq", "itertools", "functools", "operator", "re", "bisect", "string", "json", "random", "statistics",
    "decimal", "fractions", "datetime", "time", "copy", "dataclasses", "enum", "typing", "abc", "array", "queue", "numbers", "textwrap",
    "unicodedata", "types", "contextlib", "__future__", "heapq", "graphlib", "zoneinfo", "calendar", "pprint",
}
BLOCKED_BUILTINS = {"open", "exec", "eval", "compile", "input", "breakpoint", "help", "exit", "quit", "copyright", "credits", "license"}


def _restricted_builtins() -> dict:
    import builtins

    real_import = builtins.__import__

    def safe_import(name, globals=None, locals=None, fromlist=(), level=0):  # noqa: A002
        if level == 0 and name.split(".")[0] not in SAFE_IMPORTS:
            raise ImportError(f"Importing '{name.split('.')[0]}' is not allowed in practice mode (allowed: math, collections, heapq, itertools, functools, re, bisect, string, json, random, statistics, decimal, fractions, datetime, copy, dataclasses, enum, typing).")
        return real_import(name, globals, locals, fromlist, level)

    safe = {k: v for k, v in vars(builtins).items() if k not in BLOCKED_BUILTINS}
    safe["__import__"] = safe_import
    return safe


class _Capped(io.StringIO):
    def __init__(self, limit: int):
        super().__init__()
        self.limit, self.size = limit, 0

    def write(self, s: str) -> int:
        room = self.limit - self.size
        if room > 0:
            super().write(s[:room])
        self.size += len(s)
        return len(s)


def equal(actual, expected, tol: float | None) -> bool:
    """JSON-style equality. Booleans are not numbers; floats compare within `tol` (exact when tol is None)."""
    if isinstance(expected, bool) or isinstance(actual, bool):
        return isinstance(expected, bool) and isinstance(actual, bool) and expected == actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return abs(actual - expected) <= (tol or 0)
    if isinstance(expected, list):
        return isinstance(actual, list) and len(actual) == len(expected) and all(equal(a, e, tol) for a, e in zip(actual, expected, strict=True))
    if isinstance(expected, dict):
        return isinstance(actual, dict) and actual.keys() == expected.keys() and all(equal(actual[k], expected[k], tol) for k in expected)
    return actual == expected


def _alarm(ms: float):
    def handler(signum, frame):
        raise _Timeout()

    if hasattr(signal, "setitimer"):
        signal.signal(signal.SIGALRM, handler)
        signal.setitimer(signal.ITIMER_REAL, ms / 1000.0)


def _disarm():
    if hasattr(signal, "setitimer"):
        signal.setitimer(signal.ITIMER_REAL, 0)


def _err(e: BaseException) -> str:
    return f"{type(e).__name__}: {e}"[:MAX_ERROR]


def run_cases(req: dict) -> dict:
    limits = req.get("limits", {})
    per_test_ms = limits.get("per_test_ms", 2000)
    out_limit = limits.get("output_kb", 16) * 1024
    results: list[dict] = []
    started = time.perf_counter()
    namespace: dict = {"__name__": "solution"}

    def all_fail(message: str) -> dict:
        rows = [{"id": t["id"], "status": "error", "runtime_ms": None, "actual": None, "error": message[:MAX_ERROR], "stdout": None} for t in req["tests"]]
        return {"compile_error": message[:500], "tests": rows, "total_runtime_ms": round((time.perf_counter() - started) * 1000, 2)}

    try:
        code_obj = compile(req["code"], "<solution>", "exec")
    except SyntaxError as e:
        return all_fail(f"SyntaxError: {e.msg} (line {e.lineno})")
    if os.environ.get("HARNESS_MODE") == "local":
        namespace["__builtins__"] = _restricted_builtins()
    buf = _Capped(out_limit)
    try:
        with contextlib.redirect_stdout(buf):
            _alarm(per_test_ms * 2)  # top-level code gets a generous budget of its own
            exec(code_obj, namespace)  # noqa: S102 - by design: this module runs only inside a sandbox
    except _Timeout:
        return all_fail("Timeout: the top-level code took too long to run")
    except BaseException as e:  # noqa: BLE001 - includes SystemExit/KeyboardInterrupt from user code
        return all_fail(_err(e))
    finally:
        _disarm()
    fn = namespace.get(req["entry_point"])
    if not callable(fn):
        return all_fail(f"MissingFunction: define a function named {req['entry_point']}")

    for t in req["tests"]:
        buf = _Capped(out_limit)
        row = {"id": t["id"], "status": "error", "runtime_ms": None, "actual": None, "error": None, "stdout": None}
        args = copy.deepcopy(t["args"])  # a solution that mutates its input must not affect other tests
        t0 = time.perf_counter()
        try:
            with contextlib.redirect_stdout(buf):
                _alarm(per_test_ms)
                value = fn(*args)
            _disarm()
            row["runtime_ms"] = round((time.perf_counter() - t0) * 1000, 2)
            try:
                value = json.loads(json.dumps(value))  # tuples become lists, as they would in the expected JSON
            except (TypeError, ValueError):
                row["error"] = "The function returned a value that is not JSON-serializable (return lists, numbers, strings, booleans or dicts)."
            else:
                text = json.dumps(value)
                row["actual"] = text if len(text) <= MAX_ACTUAL else text[:MAX_ACTUAL]
                if "expected" in t:
                    row["status"] = "passed" if equal(value, t["expected"], t.get("tolerance")) else "failed"
                elif len(text) > MAX_FULL:
                    row["error"] = "The function returned a value that is too large to check."
                else:
                    # Sandbox mode: the expected answer is deliberately NOT in this process. The trusted runner compares outside.
                    row["status"], row["actual_full"] = "ran", text
        except _Timeout:
            row.update(status="timeout", runtime_ms=round((time.perf_counter() - t0) * 1000, 2), error=f"Exceeded {per_test_ms} ms")
        except RecursionError:
            row.update(error="RecursionError: maximum recursion depth exceeded", runtime_ms=round((time.perf_counter() - t0) * 1000, 2))
        except BaseException as e:  # noqa: BLE001 - SystemExit from sys.exit() must not end the whole run
            row.update(error=_err(e), runtime_ms=round((time.perf_counter() - t0) * 1000, 2))
        finally:
            _disarm()
        row["stdout"] = buf.getvalue()[:2000] or None
        results.append(row)
    return {"compile_error": None, "tests": results, "total_runtime_ms": round((time.perf_counter() - started) * 1000, 2)}


def apply_rlimits(memory_mb: int, cpu_s: int) -> None:
    """Hard limits for this process (soft = hard, so user code cannot raise them). Called only in sandbox mode, before user code is compiled."""
    if resource is None:
        return
    mib = 1024 * 1024
    for name, value in (
        ("RLIMIT_AS", (memory_mb + 100) * mib),  # 100 MiB of headroom for the interpreter itself
        ("RLIMIT_CPU", max(1, cpu_s)),
        ("RLIMIT_FSIZE", mib),
        ("RLIMIT_NOFILE", 64),
        ("RLIMIT_NPROC", 16),  # no fork bombs: a solution has no business starting processes
        ("RLIMIT_CORE", 0),
    ):
        try:
            resource.setrlimit(getattr(resource, name), (value, value))
        except (ValueError, OSError):  # pragma: no cover - a limit the platform refuses must not silently weaken the others
            pass


def main(argv: list[str]) -> int:
    sandbox = argv[2] == "-"  # "-": write the result to the real stdout (the trusted parent reads it) and apply hard limits
    if sandbox:
        apply_rlimits(int(os.environ.get("HARNESS_MEM_MB", "256")), int(os.environ.get("HARNESS_CPU_S", "10")))
    with open(argv[1], encoding="utf-8") as f:
        req = json.load(f)
    res = run_cases(req)
    if sandbox:
        os.write(1, (json.dumps(res) + "\n").encode())  # never sys.stdout: user code may have replaced it
        return 0
    with open(argv[2], "w", encoding="utf-8") as f:  # a file, not stdout: user code cannot corrupt it by printing
        json.dump(res, f)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
