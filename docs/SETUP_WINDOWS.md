# SETUP_WINDOWS.md: complete setup guide (final version)

One guide, start to finish. Commands are **PowerShell** unless a step says **WSL** (the Ubuntu terminal inside Windows).
**Honest status:** every step was written from, and checked against, a Linux machine (same commands in bash). **None of it has been run on Windows by me.** If something differs, send me the exact error text.
Time needed: about 40 minutes for steps 1 to 6. Step 8 (real code execution) adds about 15 minutes and is optional.

## What you get at each stage
| After step | What works |
|---|---|
| 6 | Sign up and login, resume upload and text extraction, the Lahore company directory (empty until you verify companies), coding editor (code is not executed yet), reports on whatever you have |
| 7 | Plus AI: resume analysis, practice assessments, interviews with feedback, plan wording, company research (needs the keys) |
| 8 | Plus **real code execution**: coding gets scored. Without step 8, coding always shows "Not run" and that is normal |

---

## 0. Fastest way (recommended): START.bat

1. Install Python 3.12+ and Node.js LTS once (tick "Add Python to PATH").
2. Put your keys in `apps\api\.env` (`GROQ_API_KEY`, `LLM_MODEL_PRIMARY`, `TAVILY_API_KEY`). If you already have a working `.env`, keep it.
3. Double-click `START.bat`. First time it creates the Python environment, installs packages, switches the code runner on in `.env`, migrates the database, imports the Lahore candidate list and opens three windows: **Runner**, **API**, **Web**.
4. Open http://localhost:5173. To stop, close the three windows.

Check the code runner on your PC: open any coding problem; the banner must say "Connected to the code runner (local)". Then run the starter code (it should fail a test) and a correct solution (all tests pass and a score appears). If the Runner window shows an error, send me its text.

The runner started by START.bat is the **local** backend: real execution without WSL, fine for practising on your own machine, not a hardened sandbox (see KNOWN_ISSUES). Sections 8 onward describe the stronger WSL2 sandbox, which you do not need for daily practice.

## 1. Install once
- **Python 3.12 or newer** from python.org. The project was tested on **3.12 and 3.14** (the full test suite gives the same result on both). Tick "Add python.exe to PATH". Check: `python --version` must show 3.12 or higher. If it shows an older version, install a newer one; if `py -3.12` is not found, that is fine: the commands below use plain `python`.
- **Node.js 22 LTS** from nodejs.org. Check: `node -v`
- **Git** from git-scm.com. Check: `git --version`
- **PostgreSQL** (installer from postgresql.org, any current version). Keep port 5432, set a password for the `postgres` superuser and remember it.
- *(Only for step 8)* **WSL2 with Ubuntu**. Done in step 8.

## 2. Get the project
Extract `interviewpilot-ai-final.zip` so the folder is `C:\dev\interviewpilot-ai` (the other steps assume this path; if you use another, change it everywhere). Then start version control:
```powershell
cd C:\dev\interviewpilot-ai
git init
git add .
git status --short          # make sure no .env, no storage_private, no *.db appears in this list
git commit -m "InterviewPilot AI, first snapshot"
```

## 3. Create the databases
Open **SQL Shell (psql)** from the Start menu (press Enter through the defaults, then give the `postgres` password), and run (choose your own password: letters and digits only, avoids URL problems):
```sql
CREATE ROLE interviewpilot LOGIN PASSWORD 'YOUR_DB_PASSWORD';
CREATE DATABASE interviewpilot OWNER interviewpilot;
CREATE DATABASE interviewpilot_test OWNER interviewpilot;
```
`interviewpilot_test` is only for automated tests. **The tests delete every row in it, so never point them at `interviewpilot`.**

## 4. The API (backend)
```powershell
cd C:\dev\interviewpilot-ai\apps\api
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements-dev.txt
copy .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(48))"      # copy the output
notepad .env
```
In `.env` set at least: `SECRET_KEY=<the output you copied>` and the password inside `DATABASE_URL` (it looks like `postgresql+psycopg://interviewpilot:YOUR_DB_PASSWORD@localhost:5432/interviewpilot`). Save and close, then:
```powershell
alembic upgrade head                   # creates all tables (migrations 0001 to 0009)
python -m app.cli import-seed          # 14 candidate company NAMES (none is verified)
python -m app.cli import-problems      # the 38 coding practice problems
python -m uvicorn app.main:app --reload --port 8000
```
Check in a browser: `http://localhost:8000/api/v1/health` shows `{"status":"ok","database":"ok"}`. (Interactive API docs, development only: `http://localhost:8000/docs`.)

## 5. The web app (second PowerShell window)
```powershell
cd C:\dev\interviewpilot-ai\apps\web
npm install
npm run dev                            # open http://localhost:5173
```
Keep both windows open. Always use `http://localhost:5173`, not `127.0.0.1`: login cookies and CORS are tied to that address.

## 6. Your account and admin rights
1. In the browser, sign up. 
2. Make yourself admin (in a new PowerShell window; the API can keep running):
```powershell
cd C:\dev\interviewpilot-ai\apps\api ; .\.venv\Scripts\Activate.ps1
python -m app.cli make-admin your@email.com
```
3. Log out and log in again. A **Company review** item now appears in the sidebar.

**Forgot a password?** There is no email service in this local app. Run `python -m app.cli reset-password your@email.com` and type the new password at the hidden prompt. It signs that user out everywhere. Logged-in users can change their password under **Profile and settings**.

## 7. AI keys (makes the AI features work)
Without keys the app still runs; AI features say "isn't set up".
1. **Groq** (required for resume analysis, assessments, interviews, feedback): create a key at console.groq.com (API Keys). Pick a model from https://console.groq.com/docs/models that supports JSON output and note its **exact ID**. In `apps\api\.env` set `GROQ_API_KEY=...` and `LLM_MODEL_PRIMARY=<model id>`.
2. **Tavily** (optional, only for admin company research): create a key at tavily.com. In `.env` set `TAVILY_API_KEY=...`.
3. Restart the API window (Ctrl+C, then the `uvicorn` command again).
Keep keys private: never paste them into chat, Git, screenshots or the zip. Free-tier limits may apply: one assessment makes roughly 5 to 10 AI calls and each user can start 3 an hour. I never tested the real services, so the first run is your test.

## 8. Real code execution (optional, no Docker): the runner in WSL2
The runner runs submitted Python inside a Linux sandbox (bubblewrap): no network, no access to your files, an empty environment, strict time, memory, file and process limits. It cannot run on plain Windows, so it runs inside WSL2.

**8a. Install WSL2 and Ubuntu (once).** In an **administrator** PowerShell: `wsl --install -d Ubuntu`, restart if asked, open "Ubuntu" from the Start menu and create a Linux user and password. Use that normal user (never root, never `sudo` to start the runner).

**8b. Install the sandbox tools (once).** In the **Ubuntu (WSL)** terminal:
```bash
sudo apt update && sudo apt install -y bubblewrap python3 python3-venv
```

**8c. Pick one secret and put it in the API settings.** In PowerShell: `python -c "import secrets; print(secrets.token_urlsafe(48))"`. In `apps\api\.env` set (the secret must be at least 32 characters):
```
RUNNER_MODE=http
RUNNER_URL=http://127.0.0.1:8100
RUNNER_SHARED_SECRET=<the secret>
```

**8d. Start the runner (a window that stays open).** The script reads the secret from that same `.env`:
```powershell
wsl bash /mnt/c/dev/interviewpilot-ai/scripts/start-runner.sh
```
The first run creates its own Python environment inside WSL (about a minute). You should see `Starting the code runner on http://127.0.0.1:8100 (real sandbox)`. If it prints `Refusing to start: ...`, the sandbox is not safe on this machine and it will **not** run any code; see Troubleshooting.

**8e. Check it.** In PowerShell: `Invoke-RestMethod http://127.0.0.1:8100/health` must show `backend: bwrap` and `executes_code: True`. Restart the API window. On the **Coding** page the "no code is executed" banner is gone; Run and Submit now give real pass/fail results, and reports show a real coding score.

**8f. If Windows cannot reach it.** Newer WSL2 forwards `localhost` automatically. If `Invoke-RestMethod` cannot connect, start the runner with `RUNNER_HOST=0.0.0.0` (`wsl env RUNNER_HOST=0.0.0.0 bash /mnt/c/dev/interviewpilot-ai/scripts/start-runner.sh`), find the WSL address with `wsl hostname -I`, and use `RUNNER_URL=http://<that address>:8100`. The secret still protects it.

**What the sandbox does not do.** It is strong containment for a practice tool, not a hardened judge for hostile internet users: a kernel vulnerability could in theory escape any namespace sandbox, and a program can fake its own *reported* output for tests whose answers it already knows (the visible ones), but it can never see hidden answers. See `SANDBOX_DESIGN.md` and `SECURITY_REVIEW.md`.

## 9. Verify your first real company
```powershell
cd C:\dev\interviewpilot-ai\apps\api ; .\.venv\Scripts\Activate.ps1
```
In the app open **Company review**. For a company:
1. Open the company's **own website** and find a page that shows a Lahore office (contact, about or careers). Do not rely on directory sites.
2. Select the company, fill in website, careers page and a description in your own words, **Save details**.
3. **Add location** (the locality as written on the page, tick "In Lahore").
4. **Add source**: paste the page URL, type `official_website` (or `careers_page`), label `official_verified`, tick "Shows a Lahore office", write a short note in your own words, set the date you checked.
5. Tick that source under Sources, write review notes, press **Verify as Lahore company**. If something is missing, the screen lists exactly what.
The company then appears in **Lahore companies**. Re-check every company about every 180 days; `python -m app.cli stale-check` hides overdue ones.
**Optional research (needs Tavily and Groq):** on a verified company with its website saved, press **Run research**, open every proposed link yourself, **Approve** what is correct and **Reject** the rest. Only approved findings are ever used in questions, interviews and reports.

## 10. A first full walkthrough (30 minutes)
1. **Resume** page: upload a text-based PDF or DOCX, **Analyse with AI**.
2. **Practice**: choose resume and role (and optionally a verified company) and **Write my assessment** (about a minute). Answer, **Submit**, read your results.
3. **Coding**: pick one or two problems, write Python, **Run** then **Submit**, **Finish session**.
4. **Voice interview**: tick the privacy agreement, choose typing or speaking (Chrome or Edge for speaking), answer a few questions, **End interview**, **Get feedback**.
5. **Results**: choose the role, tick the finished items, **Create report**. Try 7 and 30 days. Leave something out on purpose: the report must say it is missing.
6. Create a second report to see the comparison and the progress chart.
7. **Profile and settings**: change your password; (last) delete your account and confirm everything is gone.

## 11. Daily use
Three windows: **API** (`uvicorn`, step 4), **web** (`npm run dev`, step 5), **runner** (step 8d, optional). Stop each with Ctrl+C. Update dependencies after receiving a new zip: `pip install -r requirements-dev.txt`, `alembic upgrade head`, `npm install`.

## 12. Run the tests
```powershell
# API, quick (a temporary SQLite file). Expect about: 499 passed, 78 skipped. The skips are the sandbox tests, normal on plain Windows
cd C:\dev\interviewpilot-ai\apps\api ; .\.venv\Scripts\Activate.ps1
python -m pytest -q
python -m ruff check app tests
# API against PostgreSQL (the TEST database only). Expect the same numbers
$env:TEST_DATABASE_URL = "postgresql+psycopg://interviewpilot:YOUR_DB_PASSWORD@localhost:5432/interviewpilot_test"
python -m pytest -q
Remove-Item Env:TEST_DATABASE_URL
# Web. Expect: 137 passed
cd C:\dev\interviewpilot-ai\apps\web
npm run test ; npm run lint ; npm run build
```
**The sandbox tests** (68 tests plus the 12 hostile-program tests) only run inside WSL, as a normal user (they skip as root). In the build environment the whole suite, run as a normal user with the live runner, gave 577 passed and 0 skipped. In the **WSL** terminal:
```bash
cd /mnt/c/dev/interviewpilot-ai/apps/api
python3 -m venv ~/ip-test-venv && ~/ip-test-venv/bin/pip install -q -r requirements-dev.txt
~/ip-test-venv/bin/python -m pytest -q tests/runner
```
With the runner from step 8d running, also run the conformance suite against the live service (WSL, secret as in `.env`):
```bash
RUNNER_CONFORMANCE_URL=http://127.0.0.1:8100 RUNNER_SHARED_SECRET=<the secret> ~/ip-test-venv/bin/python -m pytest -q tests/runner/test_conformance_hostile.py
```
Expect all 12 to pass. In Windows PowerShell those 12 and the sandbox tests are skipped, which is expected.

## 13. Backup and Git
```powershell
cd C:\dev\interviewpilot-ai
git add . ; git status --short ; git commit -m "describe what changed"
git archive --format=zip --output "$HOME\Documents\interviewpilot-ai-backup.zip" HEAD
```
`.gitignore` covers `.env`, `storage_private`, databases and caches (tested). `git archive` includes tracked files only, so secrets and uploaded resumes stay out. Keep the backup outside the project folder.

## 14. Troubleshooting
| Symptom | Fix |
|---|---|
| `SECRET_KEY must be at least 32 characters` | Generate one as in step 4 and put it in `apps\api\.env` |
| `password authentication failed` | Wrong password in `DATABASE_URL`, or the role was not created (step 3) |
| `connection refused` on 5432, or health shows `"database":"unavailable"` | PostgreSQL is not running: Services app, start "postgresql-x64-..."; check `DATABASE_URL` |
| `Activate.ps1 cannot be loaded` | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Web shows "Cannot reach the server" | The API window is not running or not on port 8000 |
| Login works but you are logged out next request, or writes say "Security check failed" | Use `http://localhost:5173`, not `127.0.0.1` |
| Port already in use (8000, 5173, 8100) | `netstat -ano | findstr :8000`, then `taskkill /PID <pid> /F` |
| `alembic` cannot locate a revision | You point at an old database. Use a fresh empty one, or run `alembic upgrade head` on the right `DATABASE_URL` |
| Special characters in the DB password break the URL | Use letters and digits only, or URL-encode it |
| Upload fails with `parse_failed` or `corrupt_file` for a normal resume | Send me the exact message and your Windows version. The parser runs in a child process I could only test on Linux. Scanned (image-only) PDFs are not supported |
| "AI isn't set up" / "AI analysis isn't set up" | `GROQ_API_KEY` or `LLM_MODEL_PRIMARY` (the exact model ID) is empty in `apps\api\.env`, or the API was not restarted |
| "The AI service is unavailable" | Wrong key or model ID, no internet, rate limit, or Groq is down. The API window shows the status |
| "Live research isn't set up" or research status `unavailable` | `TAVILY_API_KEY` is empty or wrong, plan limit reached, or Tavily is down. Approved data is untouched |
| Assessment "Too few questions passed our quality checks" | The AI's questions were rejected by our checks. Try again; if it repeats, tell me the role and the model |
| Coding page says "No problems yet" | `python -m app.cli import-problems` from `apps\api` |
| Coding says "Not run" / banner "no code is executed" | The runner is not configured. Do step 8, or accept it (everything else works) |
| "The code runner is unavailable" | `RUNNER_MODE=http` but the runner window is not running, the port differs, or the two secrets differ |
| Runner prints `Refusing to start: bubblewrap is not installed` | In WSL: `sudo apt update && sudo apt install -y bubblewrap python3 python3-venv` |
| Runner prints `Refusing to start ... Do not run the runner as root` | Start it as your normal WSL user; do not use `sudo` or a root shell |
| Runner prints `Refusing to start ... uid map` or `permission denied` | Unprivileged user namespaces are blocked. In WSL try: `sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0` (only if that setting exists), then start again. If it still refuses, leave coding on "Not run": the runner will never run code unprotected |
| Runner prints `these checks failed: ...` | The sandbox is not safe on this machine. Send me the list. Do not work around it |
| `Invoke-RestMethod http://127.0.0.1:8100/health` cannot connect | See step 8f |
| `$'\r': command not found` when starting the runner | The script got Windows line endings. In WSL: `sed -i 's/\r$//' /mnt/c/dev/interviewpilot-ai/scripts/start-runner.sh` |
| Microphone does nothing | Chrome or Edge: site settings for `localhost`, allow Microphone. Firefox has no speech recognition: type instead (the app switches automatically) |
| `npm install` changes `package-lock.json` | Normal; commit the file |
| Anything else | Send the exact error text and the step number |
