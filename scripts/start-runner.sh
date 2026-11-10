#!/usr/bin/env bash
# Starts the code runner with the REAL sandbox (bubblewrap). Linux or Windows WSL2 only. Run it as your normal user, never as root.
#   From Windows PowerShell:   wsl bash /mnt/c/dev/interviewpilot-ai/scripts/start-runner.sh
#   From a WSL terminal:       bash scripts/start-runner.sh
# It reads RUNNER_SHARED_SECRET from the environment, or from apps/api/.env, so you only have to set it once.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER_DIR="$HERE/services/sandbox-runner"
VENV="${RUNNER_VENV:-$HOME/.interviewpilot-runner-venv}"   # kept inside WSL's own disk: much faster than /mnt/c
PORT="${RUNNER_PORT:-8100}"
HOST="${RUNNER_HOST:-127.0.0.1}"   # only change this if Windows cannot reach WSL on localhost; the HMAC secret still protects it

if [ "$(id -u)" -eq 0 ]; then
  echo "Do not run the runner as root or with sudo: Linux does not apply the process limit to root, so a fork bomb could exhaust this machine." >&2
  exit 1
fi
if ! command -v bwrap >/dev/null 2>&1; then
  echo "bubblewrap is not installed. Run:  sudo apt update && sudo apt install -y bubblewrap python3 python3-venv" >&2
  exit 1
fi
if [ ! -x /usr/bin/python3 ]; then
  echo "/usr/bin/python3 is missing. Run:  sudo apt install -y python3 python3-venv" >&2
  exit 1
fi

RUNNER_SHARED_SECRET="${RUNNER_SHARED_SECRET:-}"
if [ -z "$RUNNER_SHARED_SECRET" ] && [ -f "$HERE/apps/api/.env" ]; then
  # tolerate Windows line endings and quotes in the .env file
  RUNNER_SHARED_SECRET="$(grep -E '^RUNNER_SHARED_SECRET=' "$HERE/apps/api/.env" | head -1 | cut -d= -f2- | tr -d '\r"'"'"' ' || true)"
fi
if [ "${#RUNNER_SHARED_SECRET}" -lt 32 ]; then
  echo "RUNNER_SHARED_SECRET is missing or shorter than 32 characters. Set the same long random value in apps/api/.env (generate: python -c \"import secrets; print(secrets.token_urlsafe(48))\")." >&2
  exit 1
fi

if [ ! -x "$VENV/bin/python" ]; then
  echo "Creating the runner's Python environment in $VENV (first run only)..."
  /usr/bin/python3 -m venv "$VENV"
fi
"$VENV/bin/pip" install -q -r "$RUNNER_DIR/requirements.txt"

cd "$RUNNER_DIR"
export RUNNER_SHARED_SECRET RUNNER_BACKEND=bwrap
echo "Starting the code runner on http://$HOST:$PORT (real sandbox). Stop it with Ctrl+C."
exec "$VENV/bin/python" -m uvicorn runner.main:app --host "$HOST" --port "$PORT"
