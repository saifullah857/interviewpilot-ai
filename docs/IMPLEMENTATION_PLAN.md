# IMPLEMENTATION_PLAN.md

Status legend: ☐ not started · ◐ in progress · ☑ complete (all acceptance criteria checked)
Rule: no phase starts until the previous phase is approved by the user.

| Phase | Name | Status |
|---|---|---|
| 0 | Discovery & Architecture | ☑ Approved by user ("start 1"); ADR-006 still undecided |
| 1 | UI Foundation | ◐ Implemented; awaiting user verification on Windows |
| 2 | Backend Foundation & Auth | ◐ Implemented; awaiting user verification on Windows |
| 3 | Lahore Company Directory | ◐ Implemented; awaiting user verification on Windows |
| 4 | Resume Upload & Analysis | ◐ Implemented; real Groq call NOT yet exercised; awaiting user verification |
| 5 | Company Research & Role Matching | ◐ Implemented; real Tavily and Groq calls NOT yet exercised; awaiting user verification |
| 6 | Assessment Generation | ◐ Implemented; real Groq quality NOT yet seen; awaiting user verification |
| 7 | Coding Assessment | ◐ **Not complete:** pipeline built and tested; real isolated execution NOT built (ADR-006 undecided) |
| 8 | Voice Interview | ☐ |
| 9 | Scoring & Reporting | ☐ |
| 10 | Integration, QA, Security | ☐ |
| 11 | Final Delivery & Handover | ☐ |

## Phase 0 — Discovery & Architecture
Deliverables: all required docs, architecture, data model, API outline, risk/cost analysis, folder structure.
Acceptance: user reviews and approves; ADR-006 (sandbox) decided; open assumptions confirmed or changed.

## Phase 1 — UI Foundation (deps: Phase 0)
Scope: Vite/React/TS/Tailwind app, design tokens (#FB873F accent), component library, routing, landing page, dashboard shell, all required pages as routed shells with loading/empty/error/unavailable states, responsive layout, sample data clearly badged "Sample data — not verified".
Acceptance:
- `npm run dev`, `npm run build`, `npm run lint`, `npm run test` pass on user's machine.
- All 15 required page routes render without console errors at 360px and 1280px widths.
- Keyboard navigation and visible focus on nav, forms, buttons; contrast checked on primary text/accent.
- Every sample company/job is visibly labelled sample/unverified.

### Phase 1 acceptance status (checked 2026-10-14)
- ☑ `npm run build`, `npm run lint`, `npm run test` pass — **run by Claude in a Linux sandbox (Node 22.22.2), not yet on your Windows machine.**
- ☑ All 15 required page areas have routes (plus 404/not-found, empty, error, unavailable, loading states); route smoke tests render each one (21 tests pass).
- ☑ Every sample company/job/question/score is badged as sample or AI-generated practice; sample companies are fictional ("Example ...").
- ◐ Keyboard navigation / focus: skip link, visible focus ring, labelled form fields and ARIA states implemented; **not manually verified in a browser**.
- ☐ 360px and 1280px rendering and colour contrast: **not verified visually** (no browser screenshots taken). Brand orange is used as a fill with dark text, not as text on white.
- ☐ Dependency audit clean: **not clean** (see Known issues in NEXT_SESSION.md).

## Phase 2 — Backend Foundation & Auth (deps: Phase 1 optional, Phase 0 DB decision)
Scope: FastAPI skeleton, config, error model, PostgreSQL + Alembic, users, signup/login/logout/refresh, rate limiting, ownership helper, health endpoint, frontend auth wiring.
Acceptance:
- `alembic upgrade head` works on a clean DB; `pytest` passes.
- Passwords stored as Argon2id hashes; no secret in repo.
- Test proves user A cannot read user B's profile/resource by ID.
- Error responses follow the contract; no stack traces leaked.

### Phase 2 acceptance status (checked 2026-10-14)
- ☑ `alembic upgrade head` works on a clean DB (SQLite and PostgreSQL 16, in Claude's Linux sandbox); downgrade to base tested on SQLite.
- ☑ `pytest`: 30 passed on SQLite and 30 passed on PostgreSQL 16 (sandbox). `ruff check` clean.
- ☑ Passwords stored as Argon2id hashes (asserted in test); no secret in repo (`SECRET_KEY` required, placeholders rejected).
- ☑ Test proves user A cannot read user B's resource by ID (404, identical to a missing row). Uses a test-only table; real resources arrive in later phases.
- ☑ Error responses follow the contract; unhandled errors return a generic 500 without internals (tested).
- ☑ Frontend wired: login, signup, logout, route guard, profile name, voice-consent toggle, delete account. 29 frontend tests pass with the API mocked.
- ◐ Browser-to-API flow checked only with curl through the Vite proxy (health, login, /me, CSRF rejection), **not by clicking in a browser**.
- ☐ Not run on Windows.

## Phase 3 — Lahore Company Directory (deps: 2)
Scope: company/location/verification/source models, seed import CLI, search + locality filters, company detail page, admin verification workflow (minimal), evidence labels in UI.
Acceptance:
- API refuses to set `verified_lahore` without an `is_lahore` location and a recorded reviewer decision.
- Public listing endpoints return only `verified_lahore` (or explicitly labelled candidates in admin view).
- Tests: overseas-only company never listed; filter by locality; label rendering.
- Seed data labelled as seed; zero companies marked verified without evidence rows.

### Phase 3 acceptance status (checked 2026-10-14)
- ☑ API refuses `verified_lahore` without a Lahore location, an official source supporting it, notes, and a recorded reviewer (tests).
- ☑ Public endpoints return only verified Lahore companies (candidates, rejected, stale, forced-bad-data and non-Lahore locations all excluded; tests).
- ☑ Lahore-only tests exist for backend (65 API tests pass on SQLite and PostgreSQL 16) and UI (37 web tests, API mocked).
- ☑ Seed data is labelled and contains names only; a test guards that it carries no unsourced facts and that re-import never changes status.
- ☑ Search, locality/tech filters, paging, evidence labels and freshness relabelling implemented and tested.
- ◐ End-to-end workflow run live against a fresh PostgreSQL DB (signup, make-admin, seed, refused verification, successful verification, public listing) using a **fake `example.test` source in a throwaway database**.
- ☐ The admin and directory screens were **not opened in a browser**; not run on Windows.
- ☐ **No real company is verified.** That needs you (SETUP_WINDOWS.md, section 7).

## Phase 4 — Resume Upload & Analysis (deps: 2, LLM provider key)
Acceptance:
- PDF and DOCX parse into the validated schema; malformed, oversize, renamed-extension, empty, and password-protected files fail with clear errors.
- Stated vs inferred fields distinguished; resume history/version list works.
- Prompt-injection test resume (“ignore previous instructions…”) does not alter output behaviour.
- Files not reachable via any public URL; cross-user access test passes.

### Phase 4 acceptance status (checked 2026-10-15)
- ☑ PDF and DOCX parse into the validated schema; malformed, oversize, renamed-extension, empty, encrypted, macro, zip-bomb, XML-entity and scanned files fail with clear codes (111 API tests, SQLite and PostgreSQL 16).
- ☑ Stated vs inferred separated; ungrounded items dropped or downgraded; resume list and stored versions work (the UI shows only the latest version).
- ☑ Injection test resume does not change behaviour **with scripted fake models**; hijacked/extra-field output is rejected. **Not proven against a real model.**
- ☑ Files are not reachable by any URL; cross-user access returns 404; deleting a resume or account removes the stored file.
- ◐ Groq integration verified only against a local mock server (request shape, auth header, JSON mode, error mapping). **No real Groq call was made (no key).**
- ☐ Not opened in a browser; not run on Windows.

## Phase 5 — Company Research & Role Matching (deps: 3, 4, Tavily key)
Acceptance:
- Each stored finding has URL, source type, retrieved_at, label.
- Research unavailable -> graceful labelled fallback (tested with provider mocked to fail).
- Injection in a fetched page cannot change agent behaviour (test fixture).
- Unsupported claims (no source) are rejected by validator.
- Fit analysis shows matched/missing skills with reasons; no hire-probability language.

### Phase 5 acceptance status (checked 2026-10-15)
- ☑ Each stored finding/source has URL, source type, retrieval date, label (and content hash); everything starts unreviewed (175 API tests, SQLite and PostgreSQL 16).
- ☑ Research unavailable (not configured, rate limited, down) -> run recorded as `unavailable`, nothing changed, clear message (tests).
- ☑ Injection in a fetched page cannot change behaviour **with a scripted fake model**: extra/hijacked fields rejected, no new URLs fetched or saved, delimiters held (tests).
- ☑ Unsupported claims (not found in the page) are dropped; report-site findings limited to interview format.
- ☑ Fit shows matched/missing skills with reasons, sources and weights; no hire-probability wording; falls back honestly when no approved evidence.
- ◐ Live run on PostgreSQL against a **local mock of Tavily and Groq** (search, extract, AI, approval, public view, company fit, caching). **No real Tavily or Groq call was made.**
- ☐ Not opened in a browser; not run on Windows.

## Phase 6 — Assessment Generation (deps: 4, 5)
Acceptance:
- 20–30 validated questions per full assessment (configurable); schema + duplicate + answer-key checks run and logged.
- Session timer, autosave, submit, resume-later work; correct answers not exposed pre-submit.
- Every question labelled; none claims to be an actual company question unless backed by a `public_candidate_report` source (and then labelled as such with link).

### Phase 6 acceptance status (checked 2026-10-15)
- ☑ 10-30 validated questions per assessment (default 20) with schema, duplicate (also against earlier assessments), answer-key (blind second check), ambiguity and evidence checks, counts logged in the assessment (236 API tests, SQLite and PostgreSQL 16).
- ☑ Session timer (server deadline), autosave, submit, auto-submit on expiry; keys, explanations and reference points hidden until submit (tests, plus a live run).
- ☑ Honest labels: every question `ai_generated_practice` (DB-enforced); company-informed questions link their approved sources and say they are not company questions; general fallback with notice.
- ◐ Live run on PostgreSQL against a **local mock of Groq**: 20 questions written and checked (3 writing calls, 2 checking calls), test taken and submitted. **No real Groq call was made**, so real question quality is unknown.
- ☐ Not opened in a browser; not run on Windows. Short answers are not scored (Phase 9). Coding/DSA questions come in Phase 7.

## Phase 7 — Coding Assessment (deps: 6, ADR-006 decision)
Acceptance:
- Monaco editor, problem panel, run/submit, timer, results panel.
- Runner enforces CPU/memory/time/network/process limits (verified by adversarial test programs: infinite loop, fork bomb, big allocation, network call, file read outside workdir).
- FastAPI never executes user code; hidden tests never sent to browser.
- If only a mock runner exists, UI and docs say so explicitly.

### Phase 7 acceptance status (checked 2026-10-15)
- ☑ Monaco editor, problem panel, examples, constraints, language selector (Python), run, submit, results, timer, submission state (98 web tests, jsdom only).
- ☑ Problem and test-case schemas; hidden tests never sent to the browser (tests scan every response); results for hidden tests are status-only.
- ☑ FastAPI never executes user code (guard test over the whole `app/` package; the API only calls a runner).
- ☑ Runner integration contract (signed, replay-proof, validated on both sides), runner service, in-sandbox harness, and a clearly labelled mock.
- ☑ Problem bank validated: 10 problems, every reference solution passes (also under a time limit); 20 wrong solutions caught.
- ☑ Mock never reports a pass; the UI says "Nothing was run" and shows "Not run" instead of scores.
- ☐ **Runner enforces CPU/memory/time/network/process limits, verified by adversarial programs: NOT DONE.** The conformance suite is written (12 tests) and skipped. Needs ADR-006.
- ☐ Per-test timing and feedback under a real backend; Windows; real browser.
Phase 7 will be called complete only when `docs/SANDBOX_DESIGN.md` section 5 is satisfied.

### Phase 7 update (2026-10-30, Phase 12): the real runner exists
`SANDBOX_DESIGN.md` section 5 criteria 1, 2, 3, 4 (on Linux) and 6 are met; criterion 5 (you following the Windows/WSL2 setup) is **not met yet**. Coding now executes for real inside bubblewrap and reports a real score; see `SANDBOX_DESIGN.md` section 7 and `SECURITY_REVIEW.md`. Phase 7 is therefore complete **except for your verification on Windows with WSL2**.

## Phase 8 — Voice Interview (deps: 4, 5)
Acceptance:
- Consent gate before mic/transcript storage; mic denial, unsupported browser, and interrupted session paths tested and fall back to text.
- Follow-ups reference the user's prior answer; repeat-question guard tested.
- Animated visualization respects `prefers-reduced-motion`; no claims of human/facial analysis.
- Privacy notice mentions browser speech services may send audio to the browser vendor.

### Phase 8 acceptance status (checked 2026-10-24)
- ✅ Consent gate: API refuses without consent and never calls the AI first (test). Retention choice, purge after feedback and after 24 h, delete transcript, delete interview (tests).
- ✅ Mic denied, speech unsupported, speech error, quiet microphone, and interrupted-session paths tested (web and API) and fall back to typing.
- ✅ Follow-ups share content with the prior answer (guard + test); repeat-question guard tested; at most 2 follow-ups per question.
- ✅ Animation stops under `prefers-reduced-motion` (existing CSS rule covers `orb-ring` and `wave-bar`); text status always shown; no human or facial-analysis claims (opening message, notice and screens state this).
- ✅ Privacy notice mentions the browser vendor may process audio (setup page and room notice, tested).
- ☐ **Not verified:** a real microphone, real speech recognition or speech synthesis in a browser; real Groq interviewer quality; Windows. Only scripted models and a faked recognizer were used. The CSS reduced-motion behaviour was not tested in a browser.

## Phase 9 — Scoring & Reporting (deps: 6, 7, 8)
Acceptance:
- Rubrics versioned and stored; objective vs subjective separated in DB and UI.
- Report generates with missing components (e.g., no coding attempt) without error and says what is missing.
- LLM can't alter test results (test: tampered LLM output ignored).
- 7-/30-day plan and history/progress charts work.

### Phase 9 acceptance status (checked 2026-10-24)
- ✅ Rubrics versioned and stored (`report-1`, stored in each report); objective vs subjective separated in the data (`kind`) and on screen (two lists).
- ✅ Report generates with missing components and says what is missing (tests: assessment only, coding not run, no interview, no resume, nothing chosen).
- ✅ LLM cannot alter results: scores come from code with no AI; seven tampered AI plans are rejected and the scores stay identical (test).
- ✅ 7-/30-day plan (AI or built-in, labelled) and progress chart plus previous-report comparison built.
- ☐ **Not verified:** with a real Groq model (plan wording), with a real code runner (coding score), on Windows, in a real browser.
- ☐ Deferred: short-answer scoring, complexity analysis (ADR-051).

## Phase 10 — Integration, QA, Security
Acceptance: end-to-end Playwright journey passes; authorization suite passes; migrations tested up/down on clean DB; Lahore-only and label tests pass; secret scan clean; runner isolation re-tested; Windows troubleshooting guide written; critical issues fixed.

### Phase 10 acceptance status (checked 2026-10-24)
- ✅ Journey: signup to company report to progress to account deletion passes at the **API level** (`tests/test_journey.py`). ☐ **Not done:** a real-browser (Playwright) journey; browser downloads are not available in Claude's sandbox.
- ✅ Authorisation: automatic sweep of all 71 routes (open routes pinned, 401 everywhere else, admin 403, CSRF on every write); per-feature ownership tests; journey cross-user test.
- ✅ Migrations 0001 to 0008 up, down, up on **PostgreSQL 16**; no model/migration drift; full suite passes on PostgreSQL and SQLite (489 each).
- ✅ Lahore-only and label tests pass (journey and feature suites). Secret scan clean (test).
- ☐ **Runner isolation not re-tested: no real runner exists** (12 conformance tests still skipped). ☐ **Windows not verified.** ☐ Real Groq/Tavily never used.
- Fixed in this phase: vulnerable `pypdf`, PostgreSQL-only NUL server error, missing security headers, `dompurify` advisory. Full list in `SECURITY_REVIEW.md`.

## Phase 11 — Final Delivery
Acceptance: clean-machine setup instructions followed successfully by the user; source archive excludes secrets/resumes/transcripts; manifest and known-issues report complete; honest summary of tested vs untested features.

### Phase 11 acceptance status (checked 2026-10-27)
- ☐ **Clean-machine setup followed successfully by the user: not yet. Only you can do this.** What was done instead: the archive was extracted into an empty folder, a clean virtual environment was created, dependencies installed, `alembic upgrade head` run on a new database, the full backend suite run (489 passed, 12 skipped), `npm ci` and the web checks run (133 passed, build ok), and the real server started and called with `curl` (health, CSRF, signup, `/me`, roles, 10 problems, 14 candidate companies with 0 verified, security headers).
- ✅ Archive excludes secrets, resumes, transcripts and databases (secret scan; `.gitignore` tested with planted files).
- ✅ Manifest (`FILE_MANIFEST.md`) and known-issues report (`KNOWN_ISSUES.md`) complete.
- ✅ Honest summary of tested versus untested features (`HANDOVER.md`, section 2).

### Overall (updated 2026-10-30): every phase is built and the code runner now really executes code (bubblewrap, no Docker). The project is still **not production-ready**, and **nothing has been verified on your Windows machine, with WSL2, in a real browser, or against the real Groq and Tavily services**. Details: `KNOWN_ISSUES.md`.
