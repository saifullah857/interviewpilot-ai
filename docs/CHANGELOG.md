# Changelog

## 2026-11-09 (company coding sets)
- **Coding bank 38 -> 62 problems**: 24 new problems on strings, stacks, linked lists (next-pointer arrays), trees (nested `[value, left, right]` lists), two pointers, dynamic programming, graphs (BFS), heaps and backtracking: 4 easy, 10 medium and 10 hard. Every problem has a reference solution, hidden tests and wrong solutions that the hidden tests must catch (`apps/api/tests/runner/mutants_advanced.py`). Trees are limited to depth 150.
- **Company practice sets**: `GET /coding/companies/{slug}/set?role=` returns a fixed set of 25 problems (10 easy, 10 medium, 5 hard) chosen by the company's practice focus, with a "solved" mark. `POST /coding/sessions` accepts `company_set: true` (needs role and company) to take problems from that set and skip the ones you have already solved. The sets are picked from the shared bank, so problems are shared between companies; the choice differs because company focus differs. Focus is the project's own rough note, not verified company data.
- Coding problems run in Python only. SQL query problems are not offered as coding problems because the runner cannot run SQL; SQL is covered by screening questions.
- Not done: 25 problems that are unique to each company (the bank has 62 in total).

## 2026-11-08 (readiness, admin screen)
- **Company readiness** (`GET /readiness`, `/readiness/roles`, `/readiness/companies`): weighted score from skill match, role relevance, screening, assessment, coding and interview. Parts without data are "not assessed" and left out. Skill gap table with honest statuses, deterministic next actions, suggested coding problems and bank questions, best-matching companies and roles. Documented in `docs/QUESTION_BANK_AND_READINESS.md`.
- **Dashboard** shows the best roles and companies. **Manage questions** admin screen (add, edit, enable/disable, delete) for the question bank.
- Still open: 25 coding problems per company (38 shared problems exist), screening and readiness are not yet part of the automatic report, QA and Data Engineer roles, bank questions are not yet used inside the AI mock interview.

## 2026-11-07 (online screening)
- **Screening questions**: 105 multiple-choice and output questions in `data/questions/screening/screening.json` (Python, SQL, logic, JavaScript, OOP, DSA, OS, networks, Git, REST, AI/ML, cloud, QA, mobile, game). Output answers are computed by really running the code (Python, Node, SQLite) when the file is built (`python scripts/build_screening.py`), so a wrong answer cannot be written by hand. Questions are mapped to companies and roles by topic group. All are `company_focused_practice`.
- **Timed test**: `POST /screening/sessions` (role, optional company, level easy/medium/hard/mixed, 5 to 40 questions), `PUT .../answers`, `POST .../submit`, `GET .../review`. Answers are hidden until submit, the test auto-submits at the deadline, one test at a time, scored by fixed rules only (no AI). Result has score, per-topic and per-difficulty breakdown, review with explanations and a deterministic next step (adaptive difficulty and weak topics). Migration `0011`.
- **UI**: Online screening (setup, one question at a time with timer and question map, result with charts and review). Screening scores and topic strength are drawn on My progress.
- Option rule for MCQ and output questions is now an exact comparison, because `(3, 9)` and `[3, 9]` are different answers.
- Not done yet: screening results do not feed the automatic report or the company readiness score, no SQL-writing or logic sections with free text, no company match score.

## 2026-11-06 (question bank, step 1)
- **Company-wise question bank**: table `bank_questions` (migration `0010`), validated import from `data/questions/<company>.json` (`python -m app.cli import-questions`, also run by `START.bat`). Every question has a source label: `verified`, `reported` (both need a `source_note`) or `company_focused_practice`. All current questions are `company_focused_practice`; none is claimed to be a real company question.
- **Content**: 25 technical/scenario questions for each of the 21 software houses, 525 in total (easy/medium/hard mix in every company, no repeated question). All are `company_focused_practice`. Author with `scripts/qb_<company>.py`, rebuild with `python scripts/build_question_bank.py`.
- **API**: `GET /questions` (filter by company, role, category, difficulty, type, source, search), `GET /questions/stats`, `POST /questions/{slug}/reveal` (ideal answer, only on request), admin `POST/PATCH/DELETE /admin/questions` (same validation, duplicate check per company, audit log).
- **UI**: Question bank page with filters, source badge and "Show ideal answer".
- Not done yet: coding sets of 25 per company, MCQ/output screening questions, admin screen in the UI, company readiness report.

## 2026-11-05
- **Coding submit and score**: `RUNNER_MODE=local` runs submissions with the sandbox-runner local backend inside the API (a fresh child Python process per test). `START.bat` / `prepare_env.py` set it, so no separate runner window or secret is needed. Test: `test_a_real_submission_runs_and_counts_with_the_built_in_runner`.
- **Problem bank 10 -> 38**: 28 screening-style problems (list/tuple/dict/set + loops + conditions), each with a reference solution, 6+ hidden tests and 2+ wrong solutions that the hidden tests must catch. Rebuild with `python scripts/build_coding_problems.py`. New problem fields `tags` and `ds`.
- **Software-house focus + resume**: `GET /coding/companies`, `POST /coding/sessions` accepts `company` and `resume_id`. Focus tags come from `data/company_focus/focus.json` and the company seed's tech focus. Labelled `practice_focus_not_verified`. Code is run in Python only; if the resume lists another language the session says so.
- **Automatic reports**: finishing a coding session, submitting an assessment or evaluating an interview saves a report (`auto=true`, built-in plan, no AI call, does not use the manual report quota; newest 40 kept; a fuller report replaces a partial automatic one).
- **My progress** page (`GET /reports/dashboard`) with graphs; History lists saved reports. Migration `0009`.

# CHANGELOG.md

## 2026-11-02 Fix release

### Fixed
- **Code never ran and no score appeared**: `RUNNER_MODE=mock` meant submitted code was never executed. New `local` runner backend (`services/sandbox-runner/runner/backends/local.py`) runs real Python on Windows/macOS/Linux without WSL (child process per test, wall-clock kill, memory/process caps, import allow-list, expected answers never sent to the child). `START.bat` + `scripts/prepare_env.py` + `scripts/run_runner.py` switch it on automatically. This is practice-on-your-own-machine isolation, NOT the strong bubblewrap sandbox.
- **Assessment questions did not generate / timeouts / "try again" failed**: Groq provider rewritten (`app/llm/groq.py`): reasoning effort `low` for gpt-oss, output token cap, retries for timeout/5xx/429 honouring Retry-After, one try with a fallback model, no debug prints. Generation now runs small parallel batches, keeps questions when the checker is rate limited (flagged), has a time budget, and tops up from a built-in practice bank (`app/assessments/bank.py`) when the AI is slow, down or not configured, with a visible notice. Failed attempts no longer lock the user out (limit 12/hour, stale lock 5 min, Cancel button).
- **Landing page**: the numbered "flight plan" list was white text on a white card; now black on a light orange card.
- Existing unit test failure caused by debug `print` in `groq.py` removed.

### Added
- Roles: Frontend, Full-Stack Web, Backend, Mobile App developer (coding problems tagged for them; Python only).
- Lahore directory shows 21 candidates with honest status ("not checked yet" / "Lahore presence confirmed"). Technology tags on candidates are rough project notes, not verified facts.
- Any signed-in user can press **Research this company**: the agent finds the company's own domain, looks for a Lahore office on official pages and public hiring/interview info, and only then marks the Lahore presence as confirmed by an AUTOMATIC check (no human reviewer; labelled in the UI). Findings keep source labels.
- `/discover/*` API and a "Best fit for your resume" panel on the Resume page ranking roles and companies by focus area and skill overlap (a hint, not a hiring prediction).

### Changed
- Candidate (unchecked) companies can be chosen for practice, but you only get general role preparation until research confirms them. Rejected companies stay unreachable.
- Research search budget 4 -> 7 (adds a Lahore office query).

## [Unreleased]

### Phase 0 — 2026-10-14
- Added: initial versions of all required project documents plus `ARCHITECTURE.md`, `RISKS_AND_COSTS.md`, `README.md`, `.gitignore`, `.env.example`.
- No application code, no tests, no verified company data.

### Phase 1 — 2026-10-14
- Added `apps/web`: Vite + React 19 + TypeScript + Tailwind 3 app.
- Added design tokens (orange #FB873F brand, deck-navy sidebar, status colours), local fonts, reduced-motion handling.
- Added shared components: Button, LinkButton, Card, Badge, EvidenceBadge (4 labels), SampleBadge, Field, Select, Meter, Spinner, Empty/Error/Unavailable states.
- Added pages: Landing, Login, Signup, Dashboard, Companies (search + locality filter), Company detail, Resume (client-side file check only), Assessment setup/instructions/technical, Coding (Monaco, no execution), Voice interview (consent gate, visualization, text fallback; no microphone use), Results (charts), History, Settings, Not found.
- Added 21 tests (route smoke tests, filter/empty state, evidence label, interview consent gate).
- Updated docs: IMPLEMENTATION_PLAN, PROJECT_CONTEXT, DECISIONS, TASKS, FILE_MANIFEST, TEST_REPORT, NEXT_SESSION.

### Phase 2 — 2026-10-14
- Added `apps/api`: FastAPI app, settings (refuses weak/placeholder SECRET_KEY), SQLAlchemy models (users, user_profiles, refresh_tokens, audit_events), Alembic migration 0001.
- Added auth: signup, login, refresh (rotation + reuse detection), logout, CSRF double-submit, login/signup rate limits; `/me`, `/me/consents`, `DELETE /me`.
- Added ownership helper `get_owned_or_404`, uniform error format, `/health` with DB check.
- Added 30 API tests (auth, CSRF, rate limits, token forgery/expiry, ownership, error leakage, migrations up/down).
- Frontend: API client with CSRF and single-flight refresh, AuthProvider, route guard, real login/signup/logout, working Settings (name, voice consent, delete account), Vite `/api` proxy; tests grew from 21 to 29.
- Docs: SETUP_WINDOWS.md, API_CONTRACTS (implemented section), DECISIONS (ADR-014 to 016), plan/tasks/manifest/test report/next session. Replaced root `.env.example` with per-app `.env.example` files.

### Phase 3 — 2026-10-14
- Added models/migration 0002: companies, company_locations, research_sources, company_verification_records (with CHECK constraints on status, label, type).
- Added public API (`/companies`, `/companies/localities`, `/companies/{slug}`) and admin API (create, edit, locations, sources, source status, verification decisions).
- Added verification rules, label/type rules, freshness relabelling, `needs_recheck`.
- Added `app.cli` (`import-seed`, `make-admin`, `stale-check`) and `data/company_seed/lahore_candidates.json` (14 names, nothing else).
- Web: directory and detail pages now use the API (loading, error, empty and no-match states); admin "Company review" page (admin only); assessment setup lists verified companies; removed fictional sample companies.
- Tests: API 30 -> 65; web 29 -> 37.
- Docs: COMPANY_DATA_POLICY v0.2, API_CONTRACTS, DECISIONS (ADR-017 to 021), SETUP_WINDOWS section 7.

### Phase 4 — 2026-10-15
- Added migration 0003 (resumes, resume_versions), settings for storage, upload limits and the AI provider.
- Added upload pipeline: extension + magic-byte + size checks, DOCX container checks (macros, zip bombs, encryption), isolated parser process, private random-name storage, de-duplication by hash, per-user limits and rate limits.
- Added LLM layer: provider interface, Groq HTTP provider (JSON mode), scripted fake provider, validate-and-retry helper.
- Added Resume Analyst: redaction, delimited untrusted text, strict schema, evidence grounding, injection signal flags.
- Added role catalog (`data/roles/roles.json`) and deterministic fit endpoint.
- `DELETE /me` now removes stored resume files.
- Web: Resume page (upload, list, analyse, stated/inferred display, role comparison, delete), dashboard resume status.
- Tests: API 65 -> 111; web 37 -> 46.

### Phase 5 — 2026-10-15
- Migration 0004: research_runs, research_findings; research_sources gains content_hash and run_id. Settings for search provider and budgets.
- Added research providers (Tavily REST, scripted fake), per-run budget cap, deterministic URL classifier (official-domain rule, no-fetch sites, unsafe URL rejection).
- Added LangGraph research workflow with AI extraction, grounding, injection signals, Lahore scope tagging; background runs with polling, caching, per-admin rate limit, stale-run recovery; conflict detection.
- Added approval flow for findings and sources (approving a finding approves its source; rejecting a source rejects its findings).
- Company page shows approved requirements; `GET /resumes/{id}/fit` accepts `company` and returns a weighted, explained company comparison.
- Web: admin research controls and findings review; company requirements section; company selector on the Resume page.
- Tests: API 111 -> 175; web 46 -> 58.

### Phase 6 — 2026-10-15
- Migration 0005: assessments, assessment_questions, assessment_answers (label CHECK, unique positions, cascade rules).
- Added generation workflow (LangGraph) with deterministic plan, programmatic validators, blind answer check, duplicate/history awareness (weak topics, earlier questions), top-up rounds, shuffled options, evidence snapshots.
- Added assessment API (create, list, get, start, autosave answers, submit, review, delete); server-authoritative timer with grace period and lazy auto-submit; objective MCQ grading; per-user limits and rate limit; crash and stuck-run recovery.
- Web: setup page (resume, role, company, count), assessment status/instructions page with polling, test page (timer, autosave, navigator, submit confirmation), review page, real history and dashboard results.
- Fixed during development: the top-up loop never ended because the round counter was changed inside a LangGraph routing function (changes there are not kept). Counter moved into the node; recursion limit added.
- Tests: API 175 -> 236; web 58 -> 75.

### Phase 12 — 2026-10-30 (remaining work, no Docker)
- **Real code execution:** `services/sandbox-runner/runner/backends/bwrap.py` (bubblewrap namespaces, one sandbox per test, hard limits, outside deadline, comparison outside the sandbox, fail-closed startup self-check, refuses root). Harness gained a sandbox mode (limits inside, result on stdout, expected answers never sent in). Service runs code off the event loop (at most 2 at once). `scripts/start-runner.sh` starts it (tested, including a Windows-style `.env`); `.gitattributes` keeps shell scripts on LF line endings.
- **Tests:** `apps/api/tests/runner/test_bwrap_backend.py` (68 tests: hostile programs, limits, leftovers, forged replies, the whole 10-problem bank under real execution) and the 12 hostile-program conformance tests, which now actually run and pass against the live service.
- **Accounts:** `POST /me/password` (current password required, all other sessions revoked, throttled), `python -m app.cli reset-password`, and a Change password card in Settings.
- **Docs:** `SETUP_WINDOWS.md` rewritten as one linear guide (it had grown by phase); `SANDBOX_DESIGN.md` section 7; `SECURITY_REVIEW.md` runner section; ADR-058 to 061; `KNOWN_ISSUES.md`, `HANDOVER.md`, `README.md`, `NEXT_SESSION.md` updated.
- **A bug that no in-process test could see, found by running the real servers together and fixed:** the eight routes that return "204 No Content" (account deletion, logout, change password, and the deletes of assessments, resumes, coding sessions, interviews and reports) built the response with `JSONResponse(None, 204)`, which sends a stray `null` body. A real server rejects that (`Response content longer than Content-Length`) and resets the connection, so the next request on the same connection failed. Fixed with body-less responses; guarded by `tests/test_real_server.py` (a real socket, with a request after each 204) and a static check that no route builds a JSON 204.
- **Bugs found by testing and fixed:** a fork bomb exhausted memory when run as root (the runner now refuses root); a 64 KB answer cap wrongly failed a correct solution on the biggest hidden test (cap raised to 150,000); the start script crashed with a cryptic message when no secret was set; the change-password schema ignored unknown fields.
- **Totals:** backend 577 tests, all passing on PostgreSQL 16 as a normal user with the live runner (565 passed and 12 skipped without the live runner URL; 499 passed and 78 skipped where bubblewrap is unavailable). Frontend 137.

### Phase 11 — 2026-10-27
- Verified the delivered archive end to end: fresh extraction, clean virtualenv, `pip install`, `alembic upgrade head` and `alembic check` on a new database, full backend suite (489 passed, 12 skipped), `npm ci`, typecheck, lint, 133 web tests, build, `npm audit --omit=dev` (0), and a live server smoke test with `curl`.
- Verified `.gitignore` by planting `.env`, `*.db`, `storage/`, `.venv`, `node_modules`: all ignored.
- Added `docs/KNOWN_ISSUES.md` and `docs/HANDOVER.md`; rewrote `README.md`; rewrote the "Current status" section of `PROJECT_CONTEXT.md` (it had grown out of order and still said there were no uploads or assessments); appended the final inventory to `FILE_MANIFEST.md`.
- Fixed in docs: the troubleshooting table named `GROQ_MODEL`; the real setting is `LLM_MODEL_PRIMARY`.
- No application code changed in this phase.

### Phase 10 — 2026-10-24
- Added: `tests/test_security_sweep.py` (24 tests: every route's authentication, admin, CSRF; hostile-request fuzz over 1,000+ requests; headers, CORS, cookies, production mode; repository secret scan; no dynamic execution), `tests/test_journey.py` (3 tests: the whole journey, general practice, partial journey), `docs/SECURITY_REVIEW.md`.
- Added: `app/core/nul_guard.py` (NUL rejected in paths, queries and JSON bodies; 1 MiB JSON cap), a `DataError` -> 422 handler, security-header middleware.
- Fixed: `pypdf` 6.20.1 -> 6.21.2 (7 vulnerabilities). `dompurify` pinned to 3.4.17 through npm `overrides` (advisory). A NUL character caused HTTP 500 on PostgreSQL only; now a clean 400/422 on both databases.
- Changed behaviour: NUL in submitted code now returns 422 `invalid_input` (was `invalid_code`); contract updated.
- Tests: API 462 -> 489 passed (+12 skipped) on SQLite **and** on PostgreSQL 16; web 133. Migrations verified up/down/up on PostgreSQL; `alembic check` shows no drift.
- Found while testing (test-only mistakes, fixed): a deletion check queried a throw-away test table that is not in the database.

### Phase 9 — 2026-10-24
- Migration 0008: `reports`. Model, `app/reports/{rubric,compute,roadmap,schemas,service,routes}.py`; router registered; settings `reports_per_hour`, `max_reports_per_user`; `report_limiter`.
- Rubric `report-1` (docs/SCORING_RUBRICS.md): resume fit, technical knowledge, coding correctness, interview performance, problem-solving, communication, complexity (not scored); weighted overall over what exists.
- Behaviour: reports are snapshots; missing / not-run / not-scored never become numbers; gaps, strengths and practice come from stored results only; plan written by AI only if it passes strict checks, otherwise built-in; previous-report comparison; progress series.
- Web: real Results page (create report from finished work, progress chart, report list), Report page (measured vs AI judgement, gaps, strengths, plan toggle 7/30, company sources), Dashboard skill gaps and next action from real data. Removed `data/sample.ts`, the Results sample charts and the stale "Phase 1: sample data only" label.
- Fixed: a note on assessment results said short answers would be scored "with the reports"; they are not scored in this version, and the text now says so.
- Fixed while testing: when the AI's plan had unknown fields, the note wrongly said the AI was "unavailable"; it now says the plan did not pass the checks.
- Tests: API 409 -> 462 passed (+12 skipped); web 119 -> 133.

### Phase 8 — 2026-10-24
- Migration 0007: `interview_sessions`, `interview_turns`. Models, schemas, `app/interviews/{workflow,evaluate,service,routes}.py`; router registered in `main.py`; new settings (`interviews_per_hour`, `interview_ai_calls_per_hour`, `max_interviews_per_user`, `interview_idle_minutes`, `interview_purge_hours`, `interview_answer_max_chars`) and two rate limiters.
- Behaviour: consent required to start; deterministic question plan; AI interviewer (LangGraph propose -> check -> retry -> built-in fallback); follow-ups (max 2 per question); skip; client signals switch to typing; idle sessions become interrupted and can be resumed; evaluation (rubric `voice-1`) with checked turn citations; transcript retention, purge and deletion.
- Web: `lib/speech.ts`, `VoiceOrb`, Voice setup page (replaces the placeholder), interview room, feedback page, routes `/app/interview/:id` and `/app/interview/:id/review`.
- Tests: API 367 -> 409 passed (+12 skipped); web 98 -> 119.
- Fixed: `tests/test_auth.py` had two tests (`expired_or_forged_access_tokens`, `refresh_reuse`) that failed in a fresh environment because the injected cookie was added beside the real one instead of replacing it (the server correctly returned 401 when the bad cookie was alone; reproduced before fixing). Test-only change; no application code changed.
- Replaced the old single-checkbox "interview consent" web test with tests for the new setup page.

### Phase 7 — 2026-10-15 (partial: no code execution)
- Migration 0006: coding_problems, coding_sessions, coding_submissions.
- Added `services/sandbox-runner`: contract, HMAC-signed FastAPI service, mock backend, in-sandbox harness. Added `docs/SANDBOX_DESIGN.md`.
- Added problem bank (10 problems) built by `scripts/build_coding_problems.py`; importer with strict validation; `python -m app.cli import-problems`.
- Added API: problems, sessions (practice, role, or from a submitted assessment), drafts, run (visible tests), submit (all tests, hidden details withheld), finish/review, subjective AI commentary, runner status; runner client (mock and signed HTTP) with reply validation.
- Web: Coding practice list, session page (lazy Monaco, tabs, timer, autosave, results, finish dialog), results page with solutions and AI commentary, link from the assessment review; old sample coding page removed.
- Tests: API 236 -> 367 passed (+12 skipped conformance); web 75 -> 98.
- Fixed during development: a wrong-solution check showed the longest-substring problem's hidden tests could not catch a "count distinct characters" answer; two cases added. A static-guard regex produced a false positive and was tightened.
