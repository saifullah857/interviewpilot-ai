# sandbox-runner

The separate service that runs candidates' Python. The API never executes submitted code; it only sends it here, signed (HMAC).

**Backends**
- `bwrap` (real): bubblewrap namespaces. Linux, or Windows inside **WSL2**. No Docker. Needs `bubblewrap` and `/usr/bin/python3`. Must run as a normal user, never root. At startup it proves the sandbox works on this machine and **refuses to start** if it does not.
- `mock`: executes nothing; reports "Not run". The default when no runner is configured.

**Start it (the easy way)**, from Windows PowerShell (needs WSL2 with Ubuntu and `sudo apt install -y bubblewrap python3 python3-venv`, see `docs/SETUP_WINDOWS.md` step 8):
```powershell
wsl bash /mnt/c/dev/interviewpilot-ai/scripts/start-runner.sh
```
or from a Linux/WSL terminal: `bash scripts/start-runner.sh`. The script reads `RUNNER_SHARED_SECRET` from `apps/api/.env` (or the environment) and listens on `127.0.0.1:8100`.

**Start it by hand** (Linux/WSL, normal user): `RUNNER_SHARED_SECRET=<32+ chars> RUNNER_BACKEND=bwrap python -m uvicorn runner.main:app --host 127.0.0.1 --port 8100`

**Check**: `GET /health` returns `{"backend":"bwrap","executes_code":true,...}`.

Design, limits and residual risks: `docs/SANDBOX_DESIGN.md` section 7. Settings: `.env.example` here.
