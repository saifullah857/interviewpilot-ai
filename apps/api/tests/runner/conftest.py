import sys
from pathlib import Path

RUNNER_DIR = Path(__file__).resolve().parents[4] / "services" / "sandbox-runner"
if str(RUNNER_DIR) not in sys.path:
    sys.path.insert(0, str(RUNNER_DIR))
