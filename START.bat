@echo off
REM InterviewPilot AI: starts the API and the website in two windows (the code runner is built into the API). Run from the project folder.
setlocal
cd /d "%~dp0"
if not exist apps\api\.venv\Scripts\python.exe (
  echo First-time setup: creating the Python environment ...
  python -m venv apps\api\.venv || goto :fail
  apps\api\.venv\Scripts\python -m pip install --upgrade pip
  apps\api\.venv\Scripts\python -m pip install -r apps\api\requirements.txt || goto :fail
)
if not exist apps\web\node_modules (
  echo First-time setup: installing website packages ...
  pushd apps\web
  call npm install || goto :fail
  popd
)
apps\api\.venv\Scripts\python scripts\prepare_env.py || goto :fail
pushd apps\api
..\..\apps\api\.venv\Scripts\python -m alembic upgrade head || goto :fail
..\..\apps\api\.venv\Scripts\python -m app.cli import-seed
..\..\apps\api\.venv\Scripts\python -m app.cli import-problems
..\..\apps\api\.venv\Scripts\python -m app.cli import-questions
popd
start "InterviewPilot API" cmd /k "set RUNNER_MODE=local&& cd /d %~dp0apps\api && .venv\Scripts\python -m uvicorn app.main:app --port 8000"
start "InterviewPilot Web" cmd /k "cd /d %~dp0apps\web && npm run dev"
echo.
echo Two windows opened (API, Web). Open http://localhost:5173 in your browser.
echo To stop: close those two windows.
exit /b 0
:fail
echo.
echo Setup failed. Read the message above. See docs\SETUP_WINDOWS.md.
pause
exit /b 1
