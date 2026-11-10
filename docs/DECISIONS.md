# DECISIONS.md
All decisions below are **Proposed**; none is binding until the user approves Phase 0. Major deviations from the master instructions need explicit approval.

## ADR-001 Monorepo layout — Proposed
`apps/web`, `apps/api`, `services/sandbox-runner`, `docs`, `data`, `scripts`. Reason: one Git repo, one backup unit, simple for chat-based file handover. Alternative: separate repos (more overhead).

## ADR-002 Database for local development — Proposed
PostgreSQL installed natively on Windows (no Docker). SQLite permitted only for fast unit tests where behaviour is identical. Reason: master instructions require PostgreSQL; native install avoids Docker. Risk: Windows install/config friction; Phase 2 will include step-by-step instructions.

## ADR-003 Authentication — Proposed
Email + password, Argon2id hashing, short-lived access token + rotating refresh token in httpOnly SameSite cookies, CSRF protection, rate limiting. Alternative: third-party auth (adds dependency/cost); deferred.

## ADR-004 LLM provider abstraction — Proposed
`LLMProvider` interface; Groq via LangChain as first implementation; model names in env config, not code. Reason: provider-switch requirement. Groq model lineup changes often, so model choice is made at Phase 4/6 start after checking the current list.

## ADR-005 Research provider — Proposed
`ResearchProvider` interface; Tavily first (official docs list a free tier of 1,000 credits/month). Reason: built for agents; search + extract endpoints. Alternatives: Brave/Serper/SearXNG (not evaluated yet). Interview-review sites may block automated access or restrict reuse; the agent stores URLs, short paraphrased summaries and hashes, not copied reviews.

## ADR-006 Code execution isolation — **DECIDED 2026-10-30: option B, no Docker (see ADR-058)**
The master instructions forbid Docker without approval, but strong isolation of untrusted code is difficult on plain Windows. Options:
- **A. Docker Desktop (WSL2 backend) used only for the runner service.** Per-run container, `--network none`, read-only filesystem, CPU/memory/pids/time limits, non-root user. Most standard and testable. Costs: install/RAM overhead, check Docker's current licence terms for your use. Not as hardened as gVisor/Firecracker, so fine for local MVP, not for hosting public traffic.
- **B. WSL2 Linux + native sandboxing (e.g., nsjail/isolate), no Docker.** Avoids Docker but is harder to set up and I have not verified it works smoothly on your machine.
- **C. Hosted judge API (e.g., Judge0 via a vendor).** Quick, but sends user code to a third party; pricing/limits/terms not verified here.
- **D. Mock runner only until a safe option is approved.** Clearly marked development mock that does not execute arbitrary code; the integration contract is still built.
Recommendation: **A for the runner only**, with D available as the default fallback so work isn't blocked before Phase 7.

## ADR-007 Voice — Accepted (implemented in Phase 8, see "Phase 8 amendments" below)
Browser Web Speech API (speech recognition + synthesis) as primary, text input as guaranteed fallback, behind `SpeechProvider`. Caveats: recognition is not supported in all browsers, and in some browsers audio is processed by the browser vendor's servers, so the privacy notice must say so. Optional later adapter: Groq speech-to-text (free-tier terms to be verified).

## ADR-008 Frontend libraries — Proposed
React + Vite + TypeScript, Tailwind, shadcn/ui (Radix primitives, accessible), React Router, TanStack Query, `@monaco-editor/react`, Recharts, Vitest + React Testing Library, Playwright. Exact versions pinned and checked in Phase 1.

## ADR-009 File storage — Proposed
`StorageProvider` interface; local implementation writes to a private directory outside web roots with random keys; downloads only via authorized API. S3-compatible implementation possible later.

## ADR-010 Background work — Proposed
FastAPI BackgroundTasks plus a `jobs` status table with polling. No Celery/Redis for MVP. Revisit if jobs exceed request lifetimes or need retries across restarts.

## ADR-011 Company directory data — Proposed
Candidates seeded from JSON by an import script; status starts at `candidate`; `verified_lahore` requires evidence + human review (user). No UI hardcoding of companies.

## Phase 1 amendments (2026-10-14)

### ADR-008 amendment — Frontend libraries as actually built
Differences from the proposal; flagged because they deviate from ADR-008:
- **shadcn/ui and TanStack Query were NOT added.** Phase 1 uses small hand-written accessible components in `src/components/ui.tsx`. TanStack Query is deferred to Phase 2 when real API calls exist. Radix/shadcn can be added later if complex widgets (dialogs, menus) are needed.
- Fonts: Bricolage Grotesque (headings) and Public Sans (body), bundled locally via `@fontsource-variable/*` (no external font requests).
- Installed versions (resolved by npm on 2026-10-14): react 19.3.0, react-router-dom 7.18.4, vite 8.3.4, typescript 6.0.3, tailwindcss 3.4.19, recharts 3.10.1, @monaco-editor/react 4.7.0, lucide-react 1.56.0, vitest 5.0.4, eslint 10.12.0. Exact lockfile is `apps/web/package-lock.json`.

### ADR-012 Tailwind CSS pinned to v3 — Proposed
Chosen over v4 for config stability. `npm audit` flags v3's build-time dependency chain (postcss-selector-parser, braces/micromatch/chokidar). These affect the dev/build toolchain, not the shipped browser bundle. Migration to Tailwind v4 is a breaking change; decide in Phase 10 (or earlier if you prefer).

### ADR-013 Monaco loaded lazily — Accepted in code
The coding page is `React.lazy`-loaded. By default `@monaco-editor/react` fetches the Monaco editor files from a CDN at runtime, so the editor needs internet access and the CDN is a third-party dependency. Bundling Monaco locally is a Phase 7 task.

## Phase 2 amendments (2026-10-14)

### ADR-003 as built
Implemented as proposed: Argon2id (argon2-cffi defaults), 15-minute JWT access token (PyJWT, HS256, `alg` pinned) and rotating opaque refresh token (only its SHA-256 hash stored) in httpOnly SameSite=Lax cookies; double-submit CSRF token; in-memory rate limiting. Additions: refresh-token *families* with reuse detection (an old token being replayed revokes the whole family); a dummy password hash so unknown emails take similar time as wrong passwords.
Trade-offs accepted: signup returns 409 for an existing email (reveals that the email is registered; avoiding this needs email verification); in-memory rate limits reset on restart and aren't shared across processes; CSRF token isn't bound to the session.

### ADR-014 Same-origin development through Vite proxy — Accepted in code
`/api` is proxied by Vite to port 8000 so cookies are first-party and no CORS is needed in development. CORS is still configured (allow-list from `CORS_ORIGINS`) for direct access.

### ADR-015 Audit events introduced early — Accepted in code
`audit_events` table added in Phase 2 (signup, login, failed login, logout, consent change, refresh-reuse, account deletion). It stores no emails; `actor_id` becomes NULL when a user is deleted.

### ADR-016 Sync SQLAlchemy 2.x — Accepted in code
Synchronous sessions with FastAPI's threadpool. Simpler to test and reason about; revisit only if load requires it.

Installed (pinned in `apps/api/requirements.txt`): fastapi 0.143.0, uvicorn 0.54.0, SQLAlchemy 2.1.4, alembic 1.20.0, pydantic 2.14.1, pydantic-settings 2.15.0, argon2-cffi 25.1.0, PyJWT 2.15.1, psycopg 3.3.6, email-validator 2.3.0; dev: pytest 9.1.1, httpx 0.28.1, ruff 0.17.0. Transitive packages are not pinned.

## Phase 3 amendments (2026-10-14)

### ADR-017 Source review states — Accepted in code
Sources start `unreviewed`; only a verification decision (or an explicit admin status change) makes them `active` and visible. This keeps unreviewed, possibly wrong data away from users even if it was imported by a tool.

### ADR-018 Admin = a role plus a CLI to grant it — Accepted in code
There is no sign-up path to admin. `python -m app.cli make-admin <email>` grants it (audited). The company review screen is a small page under `/app/admin`, shown only to admins.

### ADR-019 Directory filtering in Python — Accepted in code
Lists are filtered and paged in Python after loading verified companies. It behaves identically on SQLite and PostgreSQL and is fine for hundreds of companies; revisit with SQL filters if the directory grows past a few thousand.

### ADR-020 Seed holds names only — Accepted
A first look for official evidence returned only third-party directory pages, so no facts were recorded. Evidence collection belongs to the admin workflow now and to the Company Research Agent in Phase 5.

### ADR-021 Freshness is computed, staleness is a command — Accepted (with a gap)
Display labels degrade automatically; moving companies to `stale` needs `stale-check`. A scheduler is not built (deferred).

### Lint note
`ruff` line length raised to 170 for the project and the Phase 3 files were auto-formatted; earlier files were not reformatted.

## Phase 4 amendments (2026-10-15)

### ADR-022 Resume Analyst is a plain function, not a LangGraph graph — Deviation from the master instructions
The flow is linear (extract -> validate -> ground). A graph would add dependencies with no extra control. LangGraph is planned where there is real branching (research in Phase 5, interview in Phase 8). Say if you want it used here anyway.

### ADR-023 Analysis is synchronous — Deviation from ADR-010
`POST /resumes/{id}/analyze` runs inside the request (provider timeout 60 s). No jobs table yet. Revisit in Phase 5 when research takes longer.

### ADR-024 Groq through plain HTTP (JSON object mode), not langchain-groq — Deviation from ADR-004
Groq's docs show an OpenAI-compatible endpoint and a JSON Object Mode that returns valid JSON but may not match a schema. Every reply is therefore validated locally with Pydantic and retried (max 2) with the error fed back. No LangChain dependency yet. The model ID is an environment setting (`LLM_MODEL_PRIMARY`) because model availability changes. Strict schema mode exists only for some models and was not used.

### ADR-025 Files are parsed in a child process — Accepted in code
`python -m app.resumes.parse_worker` runs with a timeout (20 s), a cleaned environment (no secrets), page and text caps, and a memory limit on Linux/macOS. DOCX is read with defusedxml (no DTD/entity tricks); macro, zip-bomb and encrypted files are refused before parsing. pypdf handles PDFs. Scanned PDFs are rejected (no OCR).

### ADR-026 Privacy and honesty rules for AI extraction — Accepted in code
Emails, links, phone numbers and national ID numbers are removed before text goes to the provider (names, employers and schools still go). The model must give an evidence snippet for each item; items whose snippet is not found in the resume are dropped, and "stated" skills without a matching snippet are relabelled "inferred". Resume text is delimited and treated as data; unknown output fields are rejected.

### ADR-027 Role catalog is a repo file — Accepted
`data/roles/roles.json` holds general skill lists for four roles that I wrote. They are not from any company. Role/requirement DB tables arrive in Phase 5 when company job data exists.

### ADR-028 Extracted text is stored in the database; deletion is hard — Accepted
Text is needed for re-analysis and checks. It is as sensitive as the file, and is deleted with the resume or the account (files too).

New runtime dependencies: python-multipart 0.0.32, pypdf 6.20.1, defusedxml 0.7.1, httpx 0.28.1 (now runtime). New dev: reportlab 5.0.1 (test PDFs).

## Phase 5 amendments (2026-10-15)

### ADR-029 LangGraph introduced for research — Accepted in code (as announced in ADR-022)
Graph: search -> (unavailable? stop) -> select -> (nothing? stop) -> fetch -> extract. It has real branching and does no database work (the service persists afterwards), so it is easy to test. Pinned: langgraph 1.2.15. LangChain is still not used directly.

### ADR-030 Research is admin-triggered and cached — Deviation from the user journey in the brief
The brief says the agent researches "if necessary" during a user's flow. With free-tier search credits and a human review gate, user-triggered research would spend credits per user and show unreviewed data. Instead an admin runs and approves research, and users see only approved, labelled results. Say if you want user-triggered refresh.

### ADR-031 Findings keep paraphrases, not quotes — Accepted
The AI must supply a supporting snippet; we verify it appears in the page, then discard it and keep a hash. This avoids storing third-party text while still catching unsupported claims.

### ADR-032 Background execution with BackgroundTasks and polling — Implements ADR-010
A run is a database row; the work executes in the API process; the admin page polls. Always ends in a final state (crash -> `failed`); a run stuck over 10 minutes (for example after a server restart) is marked failed on the next attempt. No retries or queue yet.

### ADR-033 Deterministic source classification and no-fetch list — Accepted
Official = the company's saved domain or its subdomains. Report sites and job boards are never fetched. See COMPANY_DATA_POLICY section 6.

### ADR-034 Role matching: deterministic with weights — Accepted (heuristics)
Company fit combines approved findings with the role: a finding applies if it is company-wide, has a generic title, or shares a distinctive word with the role title. Skill weights depend on evidence label. These are my heuristics, not validated against hiring outcomes. The matching has no AI step, so each result is explained by listed reasons and sources.

New dependency: langgraph 1.2.15 (pulls langchain-core and other packages, not pinned).

## Phase 6 amendments (2026-10-15)

### ADR-035 Generation workflow: plan -> write -> screen -> blind check -> top up — Accepted in code (LangGraph)
The mix of categories, question types and difficulty is fixed by code; the AI fills slots. Every question passes programmatic checks (shape, duplicates, content, relevance, evidence rules) and then an independent "blind" call that answers each question without seeing our key; mismatches, ambiguity and unclear questions are dropped. Up to two top-up rounds fill gaps. The loop has a hard recursion limit. Both calls use the same model, so their mistakes can be correlated: this reduces wrong keys but does not guarantee none.

### ADR-036 Honest labels are enforced by the database — Accepted
`assessment_questions.label` has a CHECK allowing only `ai_generated_practice`. Company-informed questions keep a snapshot of the approved evidence (URL and label) that inspired them. Text that claims to be a real company question is rejected.

### ADR-037 Company mode only when evidence exists — Accepted
A chosen company with no usable approved evidence gives a general assessment with a visible notice (the brief's rule: never present general prep as company-specific).

### ADR-038 Server-authoritative timer — Accepted
The deadline is set by the server when the test starts; the browser follows the server clock offset. A 30-second grace period covers network delay. Expired tests are auto-submitted lazily on the next access (including the history list) with the answers saved before the deadline.

### ADR-039 Only multiple choice is scored now — Accepted (Phase 9 scores the rest)
Short answers are stored and shown with reference points after submission, marked "not scored yet". This keeps objective results separate from subjective ones.

### ADR-040 Assessments survive resume deletion — Accepted trade-off
Deleting a resume keeps its assessments (their resume link becomes empty) so history is not lost. Questions may mention details from the resume; delete the assessment, or the account, to remove them.

### ADR-041 Background generation with polling — Reuses ADR-032
Same approach as research: a database row, work in the API process, polling, a stuck run is freed after 10 minutes.

## Phase 7 amendments (2026-10-15)

### ADR-006 status: still undecided — option D (mock) applied by default
You did not choose A, B or C before starting Phase 7, so the default agreed earlier (D) was applied. **Real code execution does not exist.** `docs/SANDBOX_DESIGN.md` describes option A in detail and defines the acceptance criteria. Docker was not available where this was written, so option A could not have been tested here in any case.

### ADR-042 Separate runner service with a signed contract — Accepted in code
The API only talks to a runner over a contract: HMAC-signed requests, 60-second clock window, replay refusal, size cap, strict schema; replies are validated against the request before use. The runner package imports nothing from the API and has no access to its secrets (tests enforce both). `RUNNER_MODE=mock` (in-process, default) or `http`.

### ADR-043 Curated problem bank, not AI-written problems — Accepted
AI-written coding tasks risk ambiguous statements and wrong tests. Ten problems were written for this project with precise ordering and tie rules, a reference solution each, and tests generated from the reference. A test-suite checks every reference against the harness and checks that 20 deliberately wrong solutions are caught by the hidden tests (and that most of them pass the visible tests, proving hidden tests matter). Problems carry the label `ai_generated_practice` (database constraint) because they were written with AI assistance and are not from any company.

### ADR-044 Hidden tests: server-side, status-only — Accepted
Hidden tests are sent to the runner (it must run them) but never to the browser, and results for them contain only a pass/fail/error/timeout status; error text and output of hidden tests are not stored. Visible tests show input, expected, actual, error and output.

### ADR-045 Correctness is objective and separate from commentary — Accepted
Correctness = tests passed in the last submission, from the runner. When code was not executed there is no score (`null`, "Not run"), never a guess. Complexity/quality commentary is optional AI text, labelled subjective, available only after the session is finished, and cannot change test results.

### ADR-046 One active coding session; server-authoritative timer — Accepted
Same timer model as assessments (30-second grace, lazy auto-finish). Limits: 30 runs per session, 5 submits per problem, 120 runner calls per hour per user.

New dependency: none in the API (httpx was already present). The runner service needs fastapi, uvicorn and pydantic.

## Phase 8 amendments (2026-10-24)
**Voice approach.** Browser speech recognition (when present) and browser speech synthesis, with typing as the guaranteed path. No server-side audio exists: the API only ever receives text. Recognised speech is placed in the answer box for the candidate to check and edit; it is never sent automatically. There is no separate `SpeechProvider` server class: the provider boundary is `apps/web/src/lib/speech.ts`, so a future provider (for example Groq speech-to-text) replaces that file without touching the interview workflow.
**Consent.** Two separate things. (1) A required per-interview agreement (answers are sent to the AI provider and held to run the interview); the API refuses to create a session without it (`consent_required`) and never contacts the AI before it. (2) A retention choice, defaulting to the Settings preference: if the transcript is not kept it is deleted right after feedback is created, or 24 hours after the interview ends (whichever comes first). Kept transcripts can be deleted at any time; the whole interview too.
**Who writes what.** The AI writes only the wording of questions and follow-ups. The mix of questions (project, technical, gap, company, behavioural) is a deterministic plan built from the resume and approved evidence. Every AI message passes programmatic checks before the candidate sees it (length, no links or markup, no claim that a question is a real company question, no instruction-like text, no near-repeat of an earlier question, a follow-up must share a content word with the answer it follows, only valid evidence numbers kept). Two failed attempts, or a provider error, produce a built-in question labelled "Built-in question". LangGraph is used here (propose -> check -> retry once -> fallback) because this is the one place the flow really branches.
**Evaluation.** Four criteria scored 0 to 4 (rubric `voice-1`), each citing candidate turn numbers that are checked against the real transcript. Citations to turns that do not exist are dropped and the criterion is marked "cites no specific answer". Unknown fields in the AI output make it invalid, so it cannot add test results or hiring claims. It judges the text of answers only: nothing is said about voice, accent, pace or appearance. The indicator is the plain average of the four scores as a percentage and is not combined with coding results (that is Phase 9).
**Interruptions.** An interview with no activity for 30 minutes becomes `interrupted`; it can be resumed (if no other interview is active and the transcript still exists) or evaluated as a partial interview. State changes go through one function with an allowed-transitions table.
**Not done on purpose.** No audio recording, no audio-level meter (the animation shows state only), no facial analysis, no proctoring.

## Phase 9 decisions (2026-10-24)
### ADR-047 Reports are immutable snapshots, computed without AI
A report stores the scores, gaps, strengths and the exact rubric used, computed once by `app/reports/compute.py` from stored results. That file contains no AI call (a test checks the source). Deleting the assessment, coding session, interview or resume afterwards leaves the report intact (the foreign keys are SET NULL). Only the roadmap can be regenerated, and doing so changes no score. Alternative considered: recompute on every view. Rejected because scores would change when a source is deleted or a rubric changes, and "progress over time" needs fixed history.
### ADR-048 Objective and subjective are separate in data and screen
Every component has `kind`. The overall indicator is a weighted average of technical knowledge (0.35, objective), coding correctness (0.35, objective) and interview performance (0.30, subjective), renormalised over what exists, and it reports its AI-judgement share. Resume fit, problem-solving and communication are shown but excluded from the overall (the first describes the document, the other two reuse interview evidence). Full definitions: `SCORING_RUBRICS.md`.
### ADR-049 Missing is not zero
`missing` (no data), `not_run` (code was submitted but the runner did not execute it) and `not_scored` (undefined) never produce a number. In particular, with the development mock runner every coding component is `not_run`. Unsubmitted problems in an otherwise executed session do count as 0 passed, and the report says so.
### ADR-050 The AI only words the plan
The plan prompt contains gap names and severities, never scores. Output with unknown fields, an unknown focus, links, out-of-range days, repeated days or instruction-like text is rejected and a built-in plan is used (labelled). If no AI is configured, reports still work. Alternative: let the AI write the whole report. Rejected: it would put an AI between stored results and the numbers you see.
### ADR-051 Deferred on purpose
Short-answer scoring (needs an AI-versus-reference-points evaluation with its own tests) and complexity analysis (needs a real runner) are not scored in report-1. The screens say so.

## Phase 10 decisions (2026-10-24)
### ADR-052 Reject NUL characters at the edge
PostgreSQL cannot store NUL in text; SQLite can. A single guard in front of the routes (paths, queries, parsed JSON including keys) gives both databases the same behaviour, and a `DataError` handler is the safety net. Alternative: validate every model field. Rejected as easy to forget on a new field. Cost: JSON bodies up to 1 MiB are parsed twice.
### ADR-053 The route list is pinned by a test
A test lists the only routes an anonymous visitor may call. A new unauthenticated route fails the build until someone deliberately adds it to that list.
### ADR-054 Test on PostgreSQL, not only SQLite
SQLite remains the quick local default, but the whole suite and the migrations are now also run on PostgreSQL 16 (`TEST_DATABASE_URL`), because the first such run found a real defect. This should stay part of the routine.
### ADR-055 No real-browser test yet
Playwright needs browser downloads that Claude's sandbox cannot make, so the journey is tested at the API level and pages with component tests. The Playwright journey is a task for your machine, not a claim.

## Phase 11 decisions (2026-10-27)
### ADR-056 Deliver as an MVP with known gaps, and say so
The project is handed over with every phase built but **not** declared complete or production-ready: real code execution does not exist (ADR-006 still needs your decision, and the master prompt forbids Docker without your approval), and nothing has been verified on your machine or against the real AI and search services. Alternatives considered: building an unapproved runner (rejected: it would break the "no Docker without approval" rule and could not be verified or safely reviewed in Claude's sandbox); presenting the UI-complete app as finished (rejected by the master prompt: "Do not claim the project is production-ready merely because the UI looks complete").
### ADR-057 The archive is verified by extraction, not by the working tree
The delivered zip is extracted into an empty folder and installed from scratch, because only that proves the archive is self-contained (all files present, lockfiles consistent, migrations complete).

## Phase 12 decisions (2026-10-30)
### ADR-058 Real code execution with bubblewrap in WSL2 (ADR-006 option B; no Docker)
You told me not to add Docker and to finish the remaining work. That leaves option B. The runner uses Linux namespaces through `bubblewrap`: on Windows it runs inside WSL2, and the API (on Windows) calls it over HTTP with HMAC signatures, as already designed. Alternatives: Docker (not approved), a hosted judge (sends code to a third party), Windows-only restrictions (Job Objects cannot block network or hide files, so it would not be real isolation). Cost: the feature needs WSL2 and works only when the runner is started; without it coding stays on the mock ("Not run"), which is still honest.
### ADR-059 The runner refuses to run as root, and fails closed
Testing showed a fork bomb exhausted the machine when the runner ran as root, because Linux exempts root-owned processes from the process-count limit. The runner now refuses to start as root, and at startup it proves nine isolation properties on the current machine; if any fails it refuses to start rather than run code unprotected.
### ADR-060 One sandbox per test, and the comparison happens outside
Each test runs in a fresh sandbox, so a hang, crash or fork bomb in one test cannot affect another, and an outside deadline can kill it even if the program ignores its own alarm. Expected answers never enter the sandbox; the trusted runner compares what the function returned. Cost: about 50 to 80 ms of start-up per test.
### ADR-061 Password reset by command line, not email
Email-based reset needs an email service (account, cost, deliverability) that a local app does not have. Instead: logged-in users change their password (current password required, all other sessions signed out) and an admin can run `python -m app.cli reset-password <email>` (hidden prompt, never an argument). Email verification is not built; it has no purpose without email.
