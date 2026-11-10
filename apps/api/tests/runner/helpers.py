"""Runs the in-sandbox harness on TRUSTED test fixtures (our own reference and deliberately wrong solutions).
Nothing here runs untrusted code, and the API itself never does."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[4] / "services" / "sandbox-runner" / "runner" / "harness.py"
BANK = Path(__file__).resolve().parents[4] / "data" / "coding" / "problems.json"


def run_harness(code: str, entry: str, tests: list[dict], per_test_ms: int = 2000, output_kb: int = 16, timeout: int = 90) -> dict:
    with tempfile.TemporaryDirectory() as d:
        req, res = Path(d) / "req.json", Path(d) / "res.json"
        req.write_text(json.dumps({"entry_point": entry, "code": code, "tests": tests, "limits": {"per_test_ms": per_test_ms, "output_kb": output_kb}}))
        subprocess.run([sys.executable, str(HARNESS), str(req), str(res)], check=True, timeout=timeout, capture_output=True)  # noqa: S603
        return json.loads(res.read_text())


def bank() -> list[dict]:
    return json.loads(BANK.read_text())["problems"]


def case(i: str, args: list, expected, tol: float | None = None) -> dict:
    return {"id": i, "args": args, "expected": expected, **({"tolerance": tol} if tol is not None else {})}
