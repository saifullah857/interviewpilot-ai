"""Starts the code runner (local backend, works on Windows without WSL). Reads the shared secret from apps/api/.env."""
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNNER = ROOT / "services" / "sandbox-runner"


def main() -> None:
    env = ROOT / "apps" / "api" / ".env"
    secret = os.environ.get("RUNNER_SHARED_SECRET", "")
    if not secret and env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            m = re.match(r"^RUNNER_SHARED_SECRET=(.*)$", line)
            if m:
                secret = m.group(1).strip().strip('"\'')
    if len(secret) < 32:
        sys.exit("RUNNER_SHARED_SECRET is missing. Run START.bat (it prepares apps\\api\\.env for you).")
    os.environ["RUNNER_SHARED_SECRET"] = secret
    os.environ.setdefault("RUNNER_BACKEND", "local")
    os.chdir(RUNNER)
    sys.path.insert(0, str(RUNNER))
    import uvicorn

    print(f"Code runner starting (backend={os.environ['RUNNER_BACKEND']}) on http://127.0.0.1:8100 . Keep this window open.")
    uvicorn.run("runner.main:app", host="127.0.0.1", port=8100, log_level="warning")


if __name__ == "__main__":
    main()
