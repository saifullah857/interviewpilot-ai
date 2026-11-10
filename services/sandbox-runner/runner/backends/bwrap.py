"""REAL EXECUTION backend: Linux namespaces through bubblewrap (`bwrap`). Needs no Docker. On Windows it runs inside WSL2.

How a submission is contained (one fresh sandbox PER TEST, so a hung or hostile test cannot affect the next one):
  - new user, pid, network, ipc, uts and cgroup namespaces; no capabilities; nested user namespaces disabled; runs as uid 65534
  - empty environment (the runner's secret and keys are never inherited); a read-only view of /usr only; no home, no /etc, no project files
  - a 16 MiB private /tmp; address-space, CPU, file-size, open-file and process-count limits set inside by the harness (soft = hard)
  - a wall-clock deadline enforced from OUTSIDE (the harness's own alarm can be ignored by hostile code); the whole sandbox is killed after it
Expected answers are never sent into the sandbox: the harness only reports what the function returned and THIS file compares it.
The runner refuses to start as root: the kernel exempts root from the process-count limit, which is what stops fork bombs.
Residual risks (documented in docs/SANDBOX_DESIGN.md): a kernel vulnerability could escape any namespace sandbox; a program can forge the
*reported* output of tests whose expected answer it already knows (the visible ones) but cannot learn hidden expected answers."""

import json
import os
import select
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from runner.contract import CaseResult, RunnerRequest, RunnerResponse
from runner.harness import equal

HARNESS = Path(__file__).resolve().parent.parent / "harness.py"
MAX_RESULT = 400_000  # JSON escaping can double the size of a 150,000-character answer
SANDBOX_UID = 65534
TMP_BYTES = 16 * 1024 * 1024
STARTUP_MARGIN_S = 1.0
ENV_ALLOWED = {"PATH", "HOME", "LANG", "PWD", "PYTHONDONTWRITEBYTECODE", "HARNESS_MEM_MB", "HARNESS_CPU_S"}  # PWD is set by bwrap itself (--chdir)

PROBE = r'''
import ctypes, json, os, socket
out = {}
try:
    s = socket.socket(); s.settimeout(2); s.connect(("1.1.1.1", 53)); out["network_blocked"] = False
except Exception:
    out["network_blocked"] = True
out["host_paths_hidden"] = not any(os.path.exists(p) for p in ("/home", "/root", "/etc/passwd", "/mnt", "/opt", "/run", "/var", "/srv"))
out["environment_clean"] = set(os.environ) <= %(allowed)r
try:
    open("/usr/probe-write", "w"); out["usr_read_only"] = False
except OSError:
    out["usr_read_only"] = True
out["unprivileged_uid"] = os.getuid() == %(uid)d and os.geteuid() == %(uid)d
caps = [l for l in open("/proc/self/status") if l.startswith("CapEff")]
out["no_capabilities"] = bool(caps) and int(caps[0].split()[1], 16) == 0
try:
    out["no_nested_userns"] = ctypes.CDLL(None, use_errno=True).unshare(0x10000000) == -1
except Exception:
    out["no_nested_userns"] = True
out["private_pid_namespace"] = os.getpid() < 10
try:
    with open("/tmp/fill", "wb") as f:
        for _ in range(40):
            f.write(b"x" * (1024 * 1024)); f.flush()
    out["tmp_is_size_limited"] = False
except OSError:
    out["tmp_is_size_limited"] = True
print(json.dumps(out))
''' % {"allowed": ENV_ALLOWED, "uid": SANDBOX_UID}


class BackendUnavailable(RuntimeError):
    """The sandbox cannot be used safely on this machine. The service refuses to start rather than run code unprotected."""


def _kill_group(proc: subprocess.Popen) -> None:
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


class BwrapBackend:
    name = "bwrap"
    version = "1"
    executes_code = True

    def __init__(self, python: str = "/usr/bin/python3", bwrap: str | None = None):
        if not sys.platform.startswith("linux"):
            raise BackendUnavailable("The bwrap backend only works on Linux. On Windows, run the runner inside WSL2 (see docs/SETUP_WINDOWS.md).")
        if os.geteuid() == 0:
            raise BackendUnavailable(
                "Do not run the runner as root (or with sudo). Linux does not apply the process-count limit to root-owned processes, so a fork bomb "
                "in a submission could exhaust this machine. Start it as your normal user."
            )
        self.bwrap = bwrap or shutil.which("bwrap") or ""
        if not self.bwrap or not Path(self.bwrap).exists():
            raise BackendUnavailable("bubblewrap is not installed. In WSL2/Ubuntu run: sudo apt install -y bubblewrap")
        self.python = python
        if not Path(python).exists() or not str(Path(python).resolve()).startswith("/usr/"):
            raise BackendUnavailable(f"{python} must exist and live under /usr (the sandbox only sees /usr). Install python3 with apt, or set RUNNER_PYTHON.")

    @classmethod
    def from_env(cls) -> "BwrapBackend":
        return cls(python=os.environ.get("RUNNER_PYTHON", "/usr/bin/python3"), bwrap=os.environ.get("RUNNER_BWRAP") or None)

    # ------------------------------------------------------------------ launching
    def _argv(self, workdir: Path, script: str, files: dict[str, bytes], mem_mb: int, cpu_s: int, script_args: list[str]) -> list[str]:
        a = [
            self.bwrap, "--unshare-user", "--unshare-pid", "--unshare-net", "--unshare-ipc", "--unshare-uts", "--unshare-cgroup-try",
            "--uid", str(SANDBOX_UID), "--gid", str(SANDBOX_UID), "--cap-drop", "ALL", "--disable-userns",
            "--die-with-parent", "--new-session", "--clearenv",
            "--setenv", "PATH", "/usr/bin", "--setenv", "HOME", "/tmp", "--setenv", "LANG", "C.UTF-8", "--setenv", "PYTHONDONTWRITEBYTECODE", "1",
            "--setenv", "HARNESS_MEM_MB", str(mem_mb), "--setenv", "HARNESS_CPU_S", str(cpu_s),
            "--ro-bind", "/usr", "/usr", "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64", "--symlink", "usr/bin", "/bin",
            "--proc", "/proc", "--dev", "/dev", "--size", str(TMP_BYTES), "--tmpfs", "/tmp",
        ]
        for name in files:
            a += ["--ro-bind", str(workdir / name), f"/work/{name}"]
        a += ["--ro-bind", str(HARNESS), "/work/harness.py", "--chdir", "/work", self.python, "-I", "-S", "-B", f"/work/{script}", *script_args]
        return a

    def _launch(self, script: str, files: dict[str, bytes], script_args: list[str], mem_mb: int, cpu_s: int, wall_s: float) -> tuple[bytes, bool, int | None, float]:
        """Run one sandbox. Returns (stdout bytes, timed_out, returncode, elapsed_ms). Never raises for anything the program does."""
        workdir = Path(tempfile.mkdtemp(prefix="ipr-"))
        try:
            os.chmod(workdir, 0o700)
            for name, data in files.items():
                (workdir / name).write_bytes(data)
            argv = self._argv(workdir, script, files, mem_mb, cpu_s, script_args)
            t0 = time.monotonic()
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, start_new_session=True, close_fds=True, env={"PATH": "/usr/bin:/bin"})  # noqa: S603
            buf, timed_out, end = b"", False, t0 + wall_s
            try:
                fd = proc.stdout.fileno()
                while True:
                    left = end - time.monotonic()
                    if left <= 0:
                        timed_out = True
                        break
                    ready, _, _ = select.select([fd], [], [], min(left, 0.05))
                    if ready:
                        chunk = os.read(fd, 65536)
                        if not chunk:
                            break  # every writer is gone: the sandbox has finished
                        buf += chunk
                        if len(buf) > MAX_RESULT:
                            timed_out = True  # a flood of output is treated like a hang: stop it
                            break
            finally:
                _kill_group(proc)
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:  # pragma: no cover
                    proc.kill()
                if proc.stdout:
                    proc.stdout.close()
            return buf, timed_out, proc.returncode, (time.monotonic() - t0) * 1000
        finally:
            shutil.rmtree(workdir, ignore_errors=True)

    # ------------------------------------------------------------------ startup check
    def self_check(self) -> dict:
        """Prove the sandbox really contains things on THIS machine. Raises BackendUnavailable (fail closed) otherwise."""
        out, timed_out, rc, _ = self._launch("probe.py", {"probe.py": PROBE.encode()}, [], 128, 10, 15)
        try:
            result = json.loads(out.decode().strip().splitlines()[-1])
        except (ValueError, IndexError):
            hint = ""
            try:  # run once more with stderr visible, only to explain a failure
                hint = subprocess.run(  # noqa: S603
                    [self.bwrap, "--unshare-user", "--unshare-pid", "--unshare-net", "--ro-bind", "/usr", "/usr", "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64", "--symlink", "usr/bin", "/bin", self.python, "-c", "pass"],
                    capture_output=True, text=True, timeout=15, env={"PATH": "/usr/bin:/bin"},
                ).stderr.strip()[:300]
            except Exception:  # noqa: BLE001
                pass
            raise BackendUnavailable(f"The sandbox could not start (exit {rc}, timed out: {timed_out}). {hint} If it mentions a uid map or permission denied, unprivileged user namespaces are disabled: see docs/SETUP_WINDOWS.md.") from None
        failed = sorted(k for k, v in result.items() if v is not True)
        if failed or len(result) < 9:
            raise BackendUnavailable("The sandbox is NOT safe on this machine; these checks failed: " + ", ".join(failed or ["probe incomplete"]))
        return result

    # ------------------------------------------------------------------ running a submission
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
            # top-level code gets 2x the per-test budget, then the test itself 1x, plus interpreter start-up
            wall = min(left, 3 * lim.per_test_ms / 1000 + STARTUP_MARGIN_S)
            cpu_s = int(3 * lim.per_test_ms / 1000) + 2
            out, timed_out, rc, elapsed = self._launch("harness.py", {"request.json": json.dumps(payload).encode()}, ["/work/request.json", "-"], lim.memory_mb, cpu_s, wall)
            result = self._parse(out)
            if result is not None and result.get("compile_error"):
                compile_error = str(result["compile_error"])[:500]
                rows = [CaseResult(id=x.id, status="error", error=compile_error) for x in req.tests]
                break
            rows.append(self._row(t, result, timed_out, rc, elapsed, lim.per_test_ms))
        total = round((time.monotonic() - started) * 1000, 2)
        return RunnerResponse(request_id=req.request_id, backend=self.name, backend_version=self.version, executed=True, compile_error=compile_error, tests=rows, total_runtime_ms=total)

    @staticmethod
    def _parse(out: bytes) -> dict | None:
        for line in reversed(out.decode("utf-8", "replace").splitlines()):
            try:
                data = json.loads(line)
            except ValueError:
                continue
            if isinstance(data, dict) and isinstance(data.get("tests"), list):
                return data
        return None

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
                ok = equal(value, t.expected, t.tolerance)  # the comparison happens HERE, outside the sandbox
                return CaseResult(id=t.id, status="passed" if ok else "failed", runtime_ms=rt, actual=r["actual_full"][:2000], stdout=out)
            return CaseResult(id=t.id, status="error", runtime_ms=rt, error=err or "The function raised an error.", stdout=out)
        ms = round(elapsed_ms, 2)
        if timed_out or (rc is not None and rc in (-signal.SIGXCPU, -signal.SIGALRM)):
            return CaseResult(id=t.id, status="timeout", runtime_ms=ms, error=f"Exceeded {per_test_ms} ms (the program did not stop when asked)")
        if rc is not None and rc < 0:
            return CaseResult(id=t.id, status="error", runtime_ms=ms, error="The program was stopped by the system (most likely it used too much memory).")
        return CaseResult(id=t.id, status="error", runtime_ms=ms, error="The program ended without reporting a result (for example it exited the interpreter or crashed).")
