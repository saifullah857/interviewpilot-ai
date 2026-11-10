"""Start with:  python -m uvicorn runner.main:app --port 8100   (set RUNNER_SHARED_SECRET first)."""
from runner.app import app_from_env

app = app_from_env()
