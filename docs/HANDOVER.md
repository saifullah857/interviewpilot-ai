# HANDOVER.md — InterviewPilot AI (2026-10-27)

## 1. What you have
A local, Lahore-focused interview-preparation web app: React/TypeScript frontend (`apps/web`), FastAPI + SQLAlchemy backend (`apps/api`, 72 endpoints, 21 tables, 8 migrations), a separate sandbox-runner service (`services/sandbox-runner`: **real code execution with bubblewrap in WSL2, no Docker**, plus a mock), seed data (`data/`) and 18 documents (`docs/`). Everything planned is built. It is a **local MVP, not production-ready, and not yet verified on your machine.** Read `KNOWN_ISSUES.md` first.

## 2. Status of every phase
| Phase | What exists | How it was checked (in Claude's sandbox) | Not checked |
|---|---|---|---|
| 0 Architecture | Plan, ADRs, data policy, risks, sandbox design | You approved it | |
| 1 UI foundation | Landing, shell, design system, responsive pages, a11y basics | 133 component/route tests, lint, typecheck, build | Real browsers, Windows |
| 2 Backend and auth | Signup/login, rotating refresh tokens, CSRF, ownership, validation, consents, account deletion | 28 auth + ownership tests; security sweep | Windows |
| 2b Account extras (Phase 12) | Change password (all other sessions signed out), admin password reset command | 6 tests + 4 web tests | Windows |
| 3 Lahore directory | Companies, locations, verification records, sources, admin review, 14 seeded **candidate** names (none verified) | 35 tests incl. Lahore-only filtering | Real company verification (your job) |
| 4 Resume | PDF/DOCX upload, safe parsing, AI extraction, role fit | 46 tests incl. hostile files | Real Groq extraction quality |
| 5 Research and matching | Admin-run research, source labels, approval flow, company-aware comparison | 64 tests incl. injection resistance | Real Tavily/Groq calls |
| 6 Assessments | Validated AI questions, timed autosaved sessions, objective MCQ scoring, review, history | 61 tests | Real Groq question quality |
| 7 Coding | Monaco editor, 10-problem bank, sessions, timer, submissions, review, signed runner contract, **real sandboxed execution (Linux/WSL2, bubblewrap)** | 58 + 46 + 27 tests; 68 sandbox tests, 12 hostile programs and the whole bank under real execution, on Linux | WSL2 itself; without WSL2 coding shows "Not run" |
| 8 Voice interview | Consent, AI interviewer with checks and fallback, browser speech + typing, interview room, evaluation, retention controls | 42 API tests + web tests | Real microphone, speech, Groq |
| 9 Scoring and reports | Rubric `report-1`, immutable reports, gaps, 7/30-day plan, comparison, progress, real Results and Dashboard | 53 tests | Real Groq plan wording |
| 10 Integration, QA, security | Journey test, all-route sweep, PostgreSQL run, audits, 4 fixes | 27 tests; suite on SQLite and PostgreSQL 16 | Real-browser journey, Windows |
| 11 Delivery | This handover, manifest, known issues, verified archive | Fresh-extract install and live-server smoke test | **You following the setup on a clean machine** |

## 3. Test summary
Backend: **577 tests, all passing on PostgreSQL 16** as a normal user with the live runner and the hostile conformance suite. Without a live runner URL: 565 passed, 12 skipped. Where bubblewrap is unavailable (plain Windows): about 499 passed, 78 skipped (the sandbox tests). SQLite gives the same results. Frontend: 137 pass. `ruff`, `eslint`, `tsc`, `vite build` clean. Migrations 0001 to 0008 apply, reverse and re-apply on PostgreSQL with no model drift. `pip-audit` clean; `npm audit --omit=dev` 0. Details: `TEST_REPORT.md`, `SECURITY_REVIEW.md`.
The archive itself is tested by extracting it into an empty folder and installing from scratch (see `TEST_REPORT.md`). **Everything above ran on Linux. Nothing ran on Windows or WSL2.**

## 4. Your first-run checklist
Follow `SETUP_WINDOWS.md` in order. In short:
1. Steps 1 to 6: install, databases, API, web, your account and admin rights (about 40 minutes).
2. Step 7: Groq key (`GROQ_API_KEY` and `LLM_MODEL_PRIMARY`, the exact model ID) and optionally Tavily.
3. Step 8 (optional, about 15 minutes): WSL2 + the runner for real code execution.
4. Step 9: verify one real Lahore company as admin. Step 10: the full walkthrough.
5. Step 12: run all the tests (and the sandbox tests inside WSL).
6. Write down everything that fails and send it with the exact error text and the step number.

## 5. Backup and Git (this is also step 13 of `SETUP_WINDOWS.md`; not run on your machine)
```powershell
cd C:\dev\interviewpilot-ai
git init                                  # first time only
git add .
git status --short                        # look: no .env, no storage_private, no *.db should be listed
git commit -m "InterviewPilot AI handover snapshot"
git archive --format=zip --output "$HOME\Documents\interviewpilot-ai-backup.zip" HEAD
```
`.gitignore` was tested: a planted `.env`, `*.db`, `storage/`, `.venv` and `node_modules` were all ignored. `git archive` includes tracked files only, so secrets and uploaded resumes stay out of the backup. Keep the backup somewhere other than the project folder.

## 6. Running it responsibly
- **Keys:** `GROQ_API_KEY`, optional `TAVILY_API_KEY` (needed for company research), and `RUNNER_SHARED_SECRET` live only in `apps\api\.env`. Rotate any key ever pasted into a chat or screenshot. Costs and rate limits of Groq and Tavily were never checked live; check the current terms yourself.
- **Company data:** verify companies manually; re-check about every 180 days (`python -m app.cli stale-check`).
- **Privacy:** answers go to the AI provider; interview transcripts are kept only if the user chooses; account deletion removes everything the user owns. Add a real privacy policy before inviting other people.
- **Do not** expose this to the internet as delivered (see `KNOWN_ISSUES.md` I8).

## 7. Continue in a new chat
Upload `docs/NEXT_SESSION.md`, `PROJECT_CONTEXT.md`, `DECISIONS.md`, `IMPLEMENTATION_PLAN.md`, `KNOWN_ISSUES.md`, `TEST_REPORT.md`, `SECURITY_REVIEW.md`, `API_CONTRACTS.md` and the latest source zip. Do not restart from scratch.

## 8. Decisions that are still yours
1. **Run it and tell me what breaks.** That is the single most valuable next step.
2. Whether you want deployment work (hosting, TLS, backups, monitoring). It needs your approval of hosting; Docker is not needed for it unless you want it.
3. Whether you want email (password reset, verification). It needs an email service account.
4. Whether someone independent should review the sandbox (`SANDBOX_DESIGN.md` section 7) before it ever runs anyone else's code.
