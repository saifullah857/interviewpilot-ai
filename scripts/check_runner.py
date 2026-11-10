"""Run this if coding says the runner is not connected. It tries to run a tiny program the same way the app does and prints why it fails.
Usage (from the project folder):  apps\\api\\.venv\\Scripts\\python scripts\\check_runner.py"""
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / "services" / "sandbox-runner"))
from runner.backends.local import LocalBackend  # noqa: E402

print("Python running this script:", sys.executable)
print("Base interpreter:", getattr(sys, "_base_executable", "(same)"))
cands = LocalBackend.candidates()
print("Interpreters to try:", cands)
ok = False
for py in cands:
    b = LocalBackend(python=py)
    try:
        b.self_check()
        print(f"OK   {py}: a program ran and an infinite loop was stopped.")
        ok = True
        break
    except Exception as e:  # noqa: BLE001
        print(f"FAIL {py}: {e}")
print("\nRESULT:", "the built-in runner works." if ok else "the built-in runner does NOT work. Send this whole output to your helper.")
sys.exit(0 if ok else 1)
