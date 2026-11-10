# NEXT_SESSION.md
_Last updated: 2026-10-30 (remaining work completed, no Docker)_

## Where the project stands
Everything planned is built, including real sandboxed code execution without Docker (bubblewrap, runs in WSL2 on Windows; ADR-058). It is a **local MVP, not production-ready, and not yet verified on the user's machine.** Read `KNOWN_ISSUES.md` first, then `HANDOVER.md`; setup is `SETUP_WINDOWS.md`.

## What was verified (Linux build environment only)
Backend 577 tests, all passing on PostgreSQL 16 as a normal user with the live runner and the 12 hostile-program tests; the whole 10-problem bank under real execution; an end-to-end run through the live API and runner producing a real coding score in a report; frontend 137 tests; lint, typecheck, build and audits clean; the delivered archive installed from scratch.

## What nobody has verified
Windows; WSL2 (the runner has never run on WSL2's kernel); a real browser, microphone and Monaco; the real Groq and Tavily services; the runner under any kernel other than the build machine's.

## Your next actions
1. Follow `SETUP_WINDOWS.md`: steps 1 to 7 and 10 first; step 8 (WSL2 + runner) after; step 12 (all tests, and the sandbox tests inside WSL).
2. Send the exact text of anything that fails, with the step number.
3. Decide if you want: deployment work, email (password reset and verification), an independent review of the sandbox before it runs anyone else's code.

## If something in the runner fails on WSL2
The runner prints why it refuses to start and never runs code unprotected. Read the three `Refusing to start` rows in the troubleshooting table. Do not work around the self-check. Files: `services/sandbox-runner/runner/backends/bwrap.py`, `scripts/start-runner.sh`, `docs/SANDBOX_DESIGN.md` section 7.

## Resume in a new chat
Upload `docs/NEXT_SESSION.md`, `PROJECT_CONTEXT.md`, `DECISIONS.md`, `IMPLEMENTATION_PLAN.md`, `KNOWN_ISSUES.md`, `TEST_REPORT.md`, `SECURITY_REVIEW.md`, `SANDBOX_DESIGN.md`, `API_CONTRACTS.md` and the latest source zip. Do not restart from scratch.
