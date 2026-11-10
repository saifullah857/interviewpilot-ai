# TASKS.md
_Last updated: 2026-10-24_

## Next actionable task
**You: follow `SETUP_WINDOWS.md` on your Windows machine (steps 1 to 7 and 10, then step 8 for real code execution) and send me the exact text of anything that fails.** Nothing else is waiting for a decision.

## In progress
- Your verification of the delivered project and of the WSL2 runner (SETUP_WINDOWS.md).
- Your verification of the delivered project (HANDOVER.md section 4).
- Phase 10 verification by user (Windows run of the full tests, a manual browser pass through the journey).
- Phase 9 verification by user (create reports with and without each component, plan 7/30, comparison, progress chart, dashboard gaps).
- Phase 8 verification by user (real microphone, speech recognition and voice, interview flow, feedback, deleting transcripts).
- Phase 7 verification by user (editor, timer, autosave, review, honest "not run" messages).

## Completed
- Remaining work (2026-10-30): real code execution without Docker (bubblewrap, ADR-058), runner start script, change password and admin reset, the setup guide rewritten as one linear guide, docs updated.
- Phase 11: fresh-extract install and live-server smoke test, KNOWN_ISSUES.md, HANDOVER.md, final manifest, README rewrite, status cleanup, one wrong variable name corrected in docs.
- Phase 10: API journey test, all-route security sweep (24 tests), NUL guard + data-error safety net, security headers, pypdf and dompurify fixes, PostgreSQL 16 run (suite + migrations), SECURITY_REVIEW.md, Windows troubleshooting.
- Phase 9: migration 0008 (reports), reports API (create, list, sources, progress, detail, regenerate plan, delete), pure score computation, checked roadmap, SCORING_RUBRICS.md, real Results and Report pages, dashboard skill gaps and next action, sample data removed; 53 new API tests, 14 new web tests.
- Phase 8: migration 0007 (interview_sessions, interview_turns), interviews API (create, answer, skip, events, end, resume, evaluate, review, delete transcript, delete), LangGraph interviewer with checks and fallback, evaluation with checked citations, speech helpers, interview setup/room/feedback pages, 42 new API tests, 21 new web tests. Also fixed two older auth tests that failed in a fresh environment (see CHANGELOG).
- Phases 0-6 (user has not yet reported results for Phases 1-6).
- Phase 7 (partial): migration 0006, problem bank (10) with validation, runner contract + signed service + harness + mock, API sessions/run/submit/review/feedback, coding pages, 367 API tests (+12 skipped conformance), 98 web tests.

## Blocked
- **Real code execution (Phase 7b): ADR-006.**

## Deferred
- Scoring of assessment short answers (not scheduled); password reset, change and email verification; unified history page; deployment; Playwright journey; more problems and languages; OCR; version history UI; durable job queue; user-triggered research; Tailwind v4; local Monaco bundling; scheduled stale-check; email verification/password reset.

## Pending
- Manual browser checks of Phases 1-7.
- After ADR-006: build the backend, run the conformance suite, re-validate the problem bank under it, write Windows instructions.
