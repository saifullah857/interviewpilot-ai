"""LOCAL PROCESS backend: real code execution on Windows, macOS or Linux WITHOUT WSL2 or Docker.

HONEST SAFETY NOTE (read this): this is NOT a security boundary like the bubblewrap backend. It is built for ONE person
practising on THEIR OWN computer. What it does:
  - one fresh child Python process PER TEST (never the API process), killed from outside when the wall-clock limit passes
  - a minimal environment (no API keys, no secrets), an empty temporary working folder that is deleted afterwards
  - the harness removes open/exec/eval/input and only allows a safe list of standard-library imports
    (math, collections, heapq, itertools, re, ...): no os, sys, subprocess, socket, ctypes, ...
  - Windows: a Job Object caps memory and allows only this one process (no child processes), and kills it on close
  - Linux/macOS: hard resource limits (memory, CPU, processes, file size)
  - expected answers are never sent into the child: it only reports what the function returned, THIS file compares it
What it cannot promise: a determined attacker who writes code to escape Python's restrictions might succeed. Do not expose
this runner to the internet or to other people. For sharing with others use the bwrap backend (Linux/WSL2).
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from runner.contract import CaseResult, RunnerRequest, RunnerResponse
from runner.harness import equal

HARNESS = Path(__file__).resolve().parent.parent / "harness.py"
MAX_RESULT = 400_000
STARTUP_MARGIN_S = 2.5  # interpreter start-up on a cold Windows machine can take a second or two
IS_WINDOWS = os.name == "nt"


def _minimal_env() -> dict[str, str]:
    env = {"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "HARNESS_MODE": "local"}
    if IS_WINDOWS:  # Python on Windows cannot start without these
        for k in ("SYSTEMROOT", "SYSTEMDRIVE", "WINDIR", "TEMP", "TMP"):
            if os.environ.get(k):
                env[k] = os.environ[k]
    else:
        env["PATH"] = "/usr/bin:/bin"
        env["LANG"] = "C.UTF-8"
    return env


# ------------------------------------------------------------------ Windows Job Object (best effort)
class _WinJob:
    """Caps memory, allows a single process and kills it when the job closes. Every failure is swallowed: the wall-clock kill still applies."""

    def __init__(self, mem_mb: int):
        self.handle = None
        if not IS_WINDOWS:
            return
        try:
            import ctypes
            from ctypes import wintypes

            class IO_COUNTERS(ctypes.Structure):
                _fields_ = [(n, ctypes.c_ulonglong) for n in ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount", "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

            class BASIC(ctypes.Structure):
                _fields_ = [
                    ("PerProcessUserTimeLimit", ctypes.c_longlong), ("PerJobUserTimeLimit", ctypes.c_longlong), ("LimitFlags", wintypes.DWORD),
                    ("MinimumWorkingSetSize", ctypes.c_size_t), ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD),
                ]

            class EXTENDED(ctypes.Structure):
                _fields_ = [
                    ("BasicLimitInformation", BASIC), ("IoInfo", IO_COUNTERS), ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t),
                ]

            k32 = ctypes.WinDLL("kernel32", use_last_error=True)
            k32.CreateJobObjectW.restype = wintypes.HANDLE
            handle = k32.CreateJobObjectW(None, None)
            if not handle:
                return
            info = EXTENDED()
            # 0x100 process memory limit | 0x8 active process limit | 0x2000 kill on job close
            info.BasicLimitInformation.LimitFlags = 0x100 | 0x8 | 0x2000
            info.BasicLimitInformation.ActiveProcessLimit = 4  # a venv python.exe starts the real python.exe as a child, so 1 would stop it from starting
            info.ProcessMemoryLimit = (mem_mb + 120) * 1024 * 1024
            ok = k32.SetInformationJobObject(handle, 9, ctypes.byref(info), ctypes.sizeof(info))  # 9 = JobObjectExtendedLimitInformation
            if not ok:
                k32.CloseHandle(handle)
                return
            self.handle, self._k32 = handle, k32
        except Exception:  # noqa: BLE001
            self.handle = None

    def attach(self, proc: subprocess.Popen) -> None:
        if self.handle:
            try:
                self._k32.AssignProcessToJobObject(self.handle, int(proc._handle))  # noqa: SLF001
            except Exception:  # noqa: BLE001
                pass

    def close(self) -> None:
        if self.handle:
            try:
                self._k32.TerminateJobObject(self.handle, 1)
                self._k32.CloseHandle(self.handle)
            except Exception:  # noqa: BLE001
                pass
            self.handle = None


def _posix_limits(mem_mb: int, cpu_s: int):
    def apply() -> None:
        import resource

        mib = 1024 * 1024
        for name, value in (("RLIMIT_AS", (mem_mb + 200) * mib), ("RLIMIT_CPU", max(1, cpu_s)), ("RLIMIT_FSIZE", mib), ("RLIMIT_NOFILE", 64), ("RLIMIT_CORE", 0)):
            try:
                resource.setrlimit(getattr(resource, name), (value, value))
            except (ValueError, OSError):
                pass
        os.setsid()

    return apply


class LocalBackend:
    name = "local"
    version = "1"
    executes_code = True

    def __init__(self, python: str | None = None):
        self.python = python or sys.executable
        self.last_stderr = ""  # what the last child printed to its error stream, kept only to explain a failed self-check

    @staticmethod
    def candidates() -> list[str]:
        """Interpreters to try, best first. Inside a venv the real interpreter is `sys._base_executable`; running it directly avoids the venv launcher."""
        found = [os.environ.get("RUNNER_PYTHON"), getattr(sys, "_base_executable", None), sys.executable]
        return list(dict.fromkeys(x for x in found if x and Path(x).exists()))

    @classmethod
    def from_env(cls) -> "LocalBackend":
        return cls(python=os.environ.get("RUNNER_PYTHON") or None)

    def _launch(self, payload: dict, mem_mb: int, cpu_s: int, wall_s: float) -> tuple[dict | None, bool, int | None, float]:
        """Run one child process. Returns (parsed result or None, timed_out, returncode, elapsed_ms). Never raises for anything the program does."""
        workdir = Path(tempfile.mkdtemp(prefix="ipr-"))
        job = _WinJob(mem_mb)
        proc = None
        err_file = None
        try:
            req_file, res_file = workdir / "request.json", workdir / "result.json"
            req_file.write_text(json.dumps(payload), encoding="utf-8")
            argv = [self.python, "-I", "-B", str(HARNESS), str(req_file), str(res_file)]
            err_file = open(workdir / "stderr.txt", "wb")  # noqa: SIM115 - closed in finally
            kwargs: dict = {"stdin": subprocess.DEVNULL, "stdout": subprocess.DEVNULL, "stderr": err_file, "cwd": str(workdir), "env": _minimal_env(), "close_fds": True}
            if IS_WINDOWS:
                kwargs["creationflags"] = 0x08000000 | 0x00000200  # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["preexec_fn"] = _posix_limits(mem_mb, cpu_s)  # noqa: PLW1509
            t0 = time.monotonic()
            proc = subprocess.Popen(argv, **kwargs)  # noqa: S603
            job.attach(proc)
            timed_out = False
            try:
                proc.wait(timeout=wall_s)
            except subprocess.TimeoutExpired:
                timed_out = True
            finally:
                self._kill(proc, job)
            elapsed = (time.monotonic() - t0) * 1000
            result = None
            if not timed_out and res_file.exists() and res_file.stat().st_size <= MAX_RESULT:
                try:
                    data = json.loads(res_file.read_text(encoding="utf-8"))
                    result = data if isinstance(data, dict) and isinstance(data.get("tests"), list) else None
                except (ValueError, OSError):
                    result = None
            return result, timed_out, proc.returncode, elapsed
        finally:
            job.close()
            try:
                if err_file is not None:
                    err_file.close()
                self.last_stderr = (workdir / "stderr.txt").read_text(encoding="utf-8", errors="replace")[-300:]
            except Exception:  # noqa: BLE001
                pass
            shutil.rmtree(workdir, ignore_errors=True)

    @staticmethod
    def _kill(proc: subprocess.Popen, job: _WinJob) -> None:
        if proc.poll() is None:
            try:
                if IS_WINDOWS:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True, timeout=10, check=False)  # noqa: S603,S607
                else:
                    import signal

                    os.killpg(proc.pid, signal.SIGKILL)
            except Exception:  # noqa: BLE001
                pass
            try:
                proc.kill()
            except Exception:  # noqa: BLE001
                pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:  # pragma: no cover
            pass

    def self_check(self) -> dict:
        """Prove a trivial program runs and an infinite loop is stopped, on THIS machine."""
        ok = self._launch({"entry_point": "f", "code": "def f():\n    return 41 + 1", "tests": [{"id": "t1", "args": []}], "limits": {"per_test_ms": 1000, "output_kb": 4}}, 128, 5, 15)[0]
        if not ok or ok["tests"][0].get("actual_full") != "42":
            raise RuntimeError(f"The local runner could not run a simple Python function with {self.python}. {self.last_stderr.strip()}".strip())
        started = time.monotonic()
        self._launch({"entry_point": "f", "code": "def f():\n    while True:\n        pass", "tests": [{"id": "t1", "args": []}], "limits": {"per_test_ms": 300, "output_kb": 4}}, 128, 3, 3)
        if time.monotonic() - started > 8:
            raise RuntimeError("The local runner could not stop an infinite loop on this machine.")
        return {"simple_function": True, "infinite_loop_stopped": True}

    def run(self, req: RunnerRequest) -> RunnerResponse:
        lim = req.limits
        started = time.monotonic()
        rows: list[CaseResult] = []
        compile_error: str | None = None
        for i, t in enumerate(req.tests):
            left = lim.total_wall_s - (time.monotonic() - started)
            if left <= 0:
                rows.extend(CaseResult(id=x.id, status="timeout", error="The total time limit was reached before this test could run.") for x in req.tests[i:])
                break
            payload = {"entry_point": req.entry_point, "code": req.code, "tests": [{"id": t.id, "args": t.args}], "limits": {"per_test_ms": lim.per_test_ms, "output_kb": lim.output_kb}}  # no `expected`
            wall = min(left, 3 * lim.per_test_ms / 1000 + STARTUP_MARGIN_S)
            cpu_s = int(3 * lim.per_test_ms / 1000) + 3
            result, timed_out, rc, elapsed = self._launch(payload, lim.memory_mb, cpu_s, wall)
            if result is not None and result.get("compile_error"):
                compile_error = str(result["compile_error"])[:500]
                rows = [CaseResult(id=x.id, status="error", error=compile_error) for x in req.tests]
                break
            rows.append(self._row(t, result, timed_out, rc, elapsed, lim.per_test_ms))
        total = round((time.monotonic() - started) * 1000, 2)
        return RunnerResponse(request_id=req.request_id, backend=self.name, backend_version=self.version, executed=True, compile_error=compile_error, tests=rows, total_runtime_ms=total)

    @staticmethod
    def _row(t, result: dict | None, timed_out: bool, rc: int | None, elapsed_ms: float, per_test_ms: int) -> CaseResult:
        """Everything in `result` came from a process that ran untrusted code, so it is re-validated and clipped. A reported 'passed' is never accepted."""
        if result is not None and len(result["tests"]) == 1 and isinstance(result["tests"][0], dict):
            r = result["tests"][0]
            status, err = r.get("status"), r.get("error")
            err = str(err)[:500] if isinstance(err, str) else None
            out = r.get("stdout")
            out = out[:2000] if isinstance(out, str) else None
            rt = r.get("runtime_ms")
            rt = round(float(rt), 2) if isinstance(rt, (int, float)) and not isinstance(rt, bool) and rt >= 0 else None
            if status == "timeout":
                return CaseResult(id=t.id, status="timeout", runtime_ms=rt, error=err or f"Exceeded {per_test_ms} ms", stdout=out)
            if status == "ran" and isinstance(r.get("actual_full"), str):
                try:
                    value = json.loads(r["actual_full"])
                except ValueError:
                    return CaseResult(id=t.id, status="error", runtime_ms=rt, error="The function's return value could not be read.", stdout=out)
                ok = equal(value, t.expected, t.tolerance)  # compared HERE, outside the child process
                return CaseResult(id=t.id, status="passed" if ok else "failed", runtime_ms=rt, actual=r["actual_full"][:2000], stdout=out)
            return CaseResult(id=t.id, status="error", runtime_ms=rt, error=err or "The function raised an error.", stdout=out)
        ms = round(elapsed_ms, 2)
        if timed_out:
            return CaseResult(id=t.id, status="timeout", runtime_ms=ms, error=f"Exceeded {per_test_ms} ms (infinite loop or too slow).")
        if rc is not None and rc != 0:
            return CaseResult(id=t.id, status="error", runtime_ms=ms, error="The program was stopped by the system (most likely it used too much memory).")
        return CaseResult(id=t.id, status="error", runtime_ms=ms, error="The program ended without reporting a result.")
