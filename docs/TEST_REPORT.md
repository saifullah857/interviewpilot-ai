# Test report

## Fix release 2026-11-02 (actually executed in the Linux build environment)
| Check | Command | Result |
|---|---|---|
| Backend | `cd apps/api; python -m pytest -q --deselect tests/test_real_server.py` | **524 passed, 78 skipped** (skips = bubblewrap sandbox tests, Linux/WSL only) |
| New: local runner backend | `tests/runner/test_local_backend.py` | 14 passed (correct/wrong/syntax, infinite loop stopped, os/subprocess/socket/open/eval refused, memory hog, secrets not inherited, reference solutions) |
| New: discover + auto research | `tests/test_discover.py` | 9 passed |
| New: question bank + resilience | `tests/test_assessments.py` | 65 passed (bank validity, checker rate-limited, AI outage fallback, retry after failure) |
| Real HTTP path | signed client -> `scripts/run_runner.py` (local backend) -> all 10 problems | every reference solution 100% of tests, a wrong solution 0%, about 0.5 s each |
| Frontend | `cd apps/web; npm run test` | **138 passed** |
| Frontend | `npx tsc -b`, `npx eslint src`, `npx vite build` | clean / clean / built |

**NOT executed:** anything on real Windows (START.bat, Windows Job Object limits, `taskkill`), real Groq or Tavily calls, a real browser/microphone, Playwright. Earlier reports below are historical.

# TEST_REPORT.md
_Last updated: 2026-10-14. Everything below was run by Claude in a Linux sandbox (Python 3.12.3, Node 22.22.2, PostgreSQL 16.15). **None of it has been run on the user's Windows machine.**_

## Phase 12 (remaining work; run by Claude in the Linux sandbox; not on Windows or WSL2)
**Python 3.14 check (2026-10-31):** every one of the 90 pinned packages has a Windows x64 wheel for CPython 3.14 at the pinned version (no compiler needed), and the full backend suite on Python 3.14.10 gave **499 passed, 78 skipped, identical to Python 3.12** (run as root, so the sandbox tests skipped). Not tested: Python 3.13, and Windows itself.

| Run | Result |
|---|---|
| Full backend suite, **PostgreSQL 16**, as an unprivileged user, live runner, conformance suite enabled | **577 passed, 0 skipped** (3 min 29 s) |
| Full backend suite, SQLite, as an unprivileged user, no live runner URL | 565 passed, 12 skipped (the 12 need the live runner URL) |
| Full backend suite, SQLite, as root (bubblewrap tests skip by design) | 499 passed, 78 skipped. This is what plain Windows without WSL2 will look like |
| 12 hostile programs against the live runner started as an unprivileged user | 12 passed in about 5 s; afterwards no sandbox processes and no temp folders |
| Whole problem bank under real sandboxed execution | all 10 reference solutions pass every visible and hidden test (each test under half its time limit); all 10 starters fail; all 21 wrong solutions caught (some by timing out) |
| Fork bomb as an unprivileged user | capped at 14 processes (`BlockingIOError`). **As root it was not contained and the machine ran out of memory**, hence the refusal to run as root |
| Real end-to-end through live API + live runner (curl-style script) | reference solution 9/9, infinite loop 0/12 and the call still returned, report showed "Coding correctness 43, 9 of 21 tests passed" with a real `stacks` gap |
| Real servers over real sockets (`tests/test_real_server.py`, and the live API + runner session) | **found a defect no in-process test could see**: the eight 204 responses carried a stray `null` body, so a real server reset the connection after them. Fixed; two new tests (real socket plus a static guard) |
| `scripts/start-runner.sh` | refuses root, refuses missing or short secret (after a bug fix), starts from a Windows-style CRLF and quoted `.env`, `/health` reports `executes_code: true` |
| Web: `vitest` / `tsc` / `eslint` | 137 passed / clean / clean |
**Not tested:** WSL2 and Windows themselves; a real browser; real Groq and Tavily; the sandbox on any kernel other than the build machine's; running more than one runner or API process.

## Phase 11 (final delivery; run by Claude in the Linux sandbox; not on Windows)
Run on the **extracted archive** in an empty folder with a clean virtualenv and a clean `npm ci`, not on the working tree:
| Check | Result |
|---|---|
| `pip install -r requirements-dev.txt` | ok (`pypdf 6.21.2`) |
| `alembic upgrade head`, `alembic current`, `alembic check` on a new SQLite database | `0008 (head)`; "No new upgrade operations detected" |
| `python -m pytest -q` | 489 passed, 12 skipped |
| `npm ci`, `tsc -b`, `eslint src`, `vitest run`, `vite build`, `npm audit --omit=dev` | clean; 133 passed; built; 0 vulnerabilities |
| Live server (`uvicorn`) with `.env`, `import-seed`, `import-problems`, then `curl` | `/health` ok with database; CSRF token issued; signup 201; `/me` 200; roles listed; 10 problems; 14 companies seeded and **0 verified**; `X-Content-Type-Options`, `X-Frame-Options`, `Cache-Control: no-store` present |
| `.gitignore` with planted `.env`, `.db`, `storage/resume.pdf`, `.venv`, `node_modules` | none tracked |
**Not done:** you following the setup on a clean Windows machine; any real-browser, real-microphone, real Groq or Tavily run; a real code runner.

## Phase 10 (run by Claude in the Linux sandbox; not on Windows)
| Command | Result |
|---|---|
| `python -m pytest -q` (SQLite) | 489 passed, 12 skipped |
| `TEST_DATABASE_URL=postgresql+psycopg://... python -m pytest -q` (**PostgreSQL 16.13**, local server) | 489 passed, 12 skipped. The first PostgreSQL run of this phase **failed** on `GET /coding/problems/%00` (HTTP 500); reproduced, fixed (ADR-052), rerun green |
| `alembic upgrade head` / `downgrade base` / `upgrade head` / `alembic check` (PostgreSQL) | head `0008`; reverse and re-apply succeed; "No new upgrade operations detected" |
| `pip-audit -r requirements.txt` | before: 7 vulnerabilities in pypdf 6.20.1; after pinning 6.21.2: none |
| `npm audit --omit=dev` | before: dompurify (critical) via Monaco; after override 3.4.17: 0 vulnerabilities. `npm audit` (all): 3 moderate in Tailwind v3 build tooling, accepted |
| `ruff check app tests`, `tsc -b`, `eslint src`, `npx vitest run`, `vite build` | clean; 133 web tests passed; build ok |
The 12 skipped tests are the hostile-program runner suite (needs a real runner). **Not tested:** Windows; a real browser (no Playwright); real Groq/Tavily; a real code runner; more than one API process (rate limits are in memory).

## Phase 9 (run by Claude in the Linux sandbox; not on Windows)
| Command | Result |
|---|---|
| `python -m pytest -q` (SQLite) | 462 passed, 12 skipped (409 before; 53 new in `tests/test_reports.py`, including migration 0008 up/down). Not run against PostgreSQL this time. |
| `ruff check app tests` | All checks passed |
| `npx vitest run` / `tsc -b` / `eslint src` / `vite build` | 133 passed (119 before) / clean / clean / ok |
Covered: missing components, `not_run` coding with the mock runner, real scores with a scripted runner, weighted overall maths, ownership of every source and report, role mismatch, tampered AI plans (7 cases), no-AI fallback, built-in plans for 0 to 8 gaps in both horizons, snapshots surviving source deletion, comparison, progress, company evidence rules, limits.
**Not tested:** real Groq plan wording; a real code runner (a scripted double stands in); Windows; PostgreSQL for this phase; pages in a real browser. The weights in the overall indicator are a judgement, not validated.

## Phase 8 (run by Claude in the Linux sandbox; not on Windows)
| Command | Result |
|---|---|
| `python -m pytest -q` (SQLite) | 409 passed, 12 skipped (same hostile-program suite as Phase 7). Not run against PostgreSQL this time. |
| `python -m pytest -q tests/test_interviews.py tests/test_migrations.py` | 43 passed (migration 0007 up/down included) |
| `ruff check app tests` | All checks passed |
| `npx vitest run` / `tsc -b` / `eslint src` / `vite build` | 119 passed / clean / clean / ok |
Before changing anything, a baseline run showed 1 then 2 failing auth tests (duplicate cookie in the test client). Reproduced, root cause was in the tests, fixed there.
**Not tested:** a real microphone; real `SpeechRecognition` or `speechSynthesis` (a hand-written fake recognizer was used); real Groq output (scripted model only); reduced-motion CSS in a browser; Windows; PostgreSQL for this phase; the pages in a real browser. The follow-up "references the prior answer" check is a shared-word heuristic, not a semantic test.

## Phase 7 (run by Claude in the Linux sandbox; not on Windows)
| Command | Result |
|---|---|
| `python -m pytest -q` (SQLite) | 367 passed, 12 skipped (the hostile-program conformance suite, which needs a real isolated backend) |
| same with `TEST_DATABASE_URL` -> PostgreSQL 16 | 367 passed, 12 skipped |
| `ruff check .` | All checks passed |
| `npm run test` (3 runs) / `lint` / `tsc -b` / `build` | 98 passed each time / clean / clean / ok (Monaco and the session page load as a separate lazy chunk) |
| Live run: PostgreSQL + the **API and the runner service as two separate processes over signed HTTP** (mock backend) | Worked: runner status "mock, executes_code false"; session created; Run and Submit returned `not_executed` / `not_run` with no pass counts; a submission containing code that would create a file did **not** create it; hidden rows contained only id/label/status; review was locked (409) until finish, then showed the solution; the runner log shows 2 signed requests accepted |

What the Phase 7 tests cover: harness (pass/fail, stdout capture and caps, exceptions, `sys.exit` in user code, syntax errors, missing function, slow code and timeouts that `except Exception` cannot swallow, non-JSON results, tuples/bools/float tolerance, fresh argument copies, recursion, truncation); runner service (signature, tampering, stale/future timestamps, replay, size and schema limits, weak secret, mock never executes code, no imports from the API); problem bank (shape, role coverage, no hidden test duplicates a visible one, request size, every reference solution passes quickly, starter code fails, 20 wrong solutions all caught, most of them pass the visible tests); API (ownership, CSRF, limits, drafts, visible-only runs, hidden redaction in every response and in stored data, errors and output of hidden tests not leaked, runner down, untrustworthy replies discarded for 8 kinds of violation, mock never reports a pass, timer and auto-finish, sessions from assessments, review lock, AI commentary labelling/caching/validation/injection handling, vendored contract equals the runner's, the API package contains no code-execution calls).
**Test-suite finding:** the wrong-solution check exposed that the longest-substring problem's hidden tests missed one wrong answer; two hidden cases were added and the check now passes.
**Not tested, and why this phase is incomplete:** any real isolated execution. The harness was exercised only with trusted fixtures (my own reference and wrong solutions) in this sandbox, which has no Docker. Per-test timeouts, memory and output limits, network and filesystem isolation, process limits and cleanup have not been verified under any real backend. The hostile conformance suite exists but is skipped. Real Groq output for AI commentary, real browser behaviour, and Windows are also untested.

## Phase 6 (run by Claude in the Linux sandbox; not on Windows)
| Command | Result |
|---|---|
| `python -m pytest -q` (SQLite) | 236 passed |
| same with `TEST_DATABASE_URL` -> PostgreSQL 16 | 236 passed |
| `ruff check .` | All checks passed |
| `npm run test` (4 runs in a row) / `lint` / `tsc -b` / `build` | 75 passed each time / clean / clean / ok |
| Live run: PostgreSQL 16 + uvicorn + **local mock of Groq** (scripted question writer and checker) | Worked: 20 questions written (3 writing calls) and checked (2 checking calls); questions hidden before start; keys hidden while running; review blocked until submit (409); autosave 200; submit scored multiple choice; history showed the score; the resume's email address never reached the provider |

**Bugs found by the tests and fixed:** (1) the top-up loop never terminated, because the round counter was updated inside a LangGraph routing function whose changes are discarded (found when a test hung); the counter now changes inside the node and a recursion limit backs it up. (2) Core role skills could be cut from the technical focus list when the resume already showed them; fixed. Two web test races (not app bugs) were also fixed.
**Not tested: any call to the real Groq service**, so the quality of real generated questions, how often the real model passes our checks, and how many questions get discarded are all unknown.
Coverage: creation rules (ownership, analysed resume, role, verified company, counts, AI not configured), generation (balance, labels, shuffling, uniqueness, hidden keys), timer (deadline, idempotent start, grace, auto-submit), autosave and validation, grading and review, ownership (404 on every route), deletion cascades, limits (one at a time, stuck release, rate, storage), crash/AI-outage/insufficient-questions handling, every validator (shape, duplicates, vague options, URLs/markup, injection phrases, fake "was asked at" claims, off-topic, evidence rules), blind check (key mismatch, ambiguity, unclear, missing or garbled replies, checker never sees the key), top-up rounds and their stop condition, hijacked output, delimiter escape, plan arithmetic, company evidence selection (approved, current, relevant only), general fallback notice, history (weak topics, no repeats), DB label constraint. Web (API mocked): setup, status pages, taking the test (labels, autosave, restore, failure retry, confirmation, auto-submit, server clock, time-expired redirect), review, history, dashboard.
Limits: autosave debounce and the timer were tested in jsdom only, not in a real browser. Prompt-injection behaviour was tested with scripted fakes only.

## Phase 5 (run by Claude in the Linux sandbox; not on Windows)
| Command | Result |
|---|---|
| `python -m pytest -q` (SQLite) | 175 passed |
| same with `TEST_DATABASE_URL` -> PostgreSQL 16 | 175 passed |
| `ruff check .` | All checks passed |
| `npm run test` / `lint` / `tsc -b` / `build` | 58 passed / clean / clean / ok |
| Live run: PostgreSQL 16 + uvicorn + **local mock of Tavily (/search, /extract) and Groq** | Worked: research started (202), ran in the background (4 searches, 1 fetch), saved 2 sources + 2 findings as unreviewed, users saw nothing until approval, then saw labelled requirements; company fit computed; a second request was served from cache. The mock confirmed Bearer auth and that the report site was not fetched. The company was "verified" with a fake `example.com` source in a throwaway database |

**Not tested: any call to the real Tavily or Groq services.** Tavily's request/response shape was checked against its official API reference only.
Coverage: classifier (official vs look-alike hosts, userinfo trick, IPs/localhost/internal/non-http, report sites, job boards, canonical URLs), Tavily provider (request body, parsing, error mapping, no key leakage), budget cap, workflow (grounding, dropped irrelevant pages, no-fetch sites, kind limits, injection page, hijacked output, outages, no results, no official site, AI failures, source caps), API (admin-only, unverified refused, full run, approval gating, source rejection cascade, stale relabelling, caching/force, no duplicates on re-run, outage, partial, insufficient, crash handling, 503 when unconfigured, concurrency and dead-run recovery, rate limit, conflicts), company fit (weights, reasons, role filtering, no evidence, verified-only, outdated evidence), title heuristic, company deletion cascade. Web (API mocked): research states and polling (fake timers), approvals, requirements display, company comparison.
Limits: injection behaviour tested with scripted fakes only. Search quality for real Lahore companies is unknown.

## Phase 4 (run by Claude in the Linux sandbox; not on Windows)
| Command | Result |
|---|---|
| `python -m pytest -q` (SQLite) | 111 passed |
| same with `TEST_DATABASE_URL` -> PostgreSQL 16 | 111 passed |
| `ruff check .` | All checks passed |
| `npm run test` / `lint` / `tsc -b` / `build` | 46 passed / clean / clean / ok |
| Live run: PostgreSQL + uvicorn + a **local mock of Groq's API** on port 9100; upload a real generated PDF, analyse, fit | Worked. The mock confirmed: path `/openai/v1/chat/completions`, `Authorization: Bearer ...`, `response_format: json_object`, configured model, and that the email address never appeared in the request. File stored as a 32-character name without extension |

**Not tested: any call to the real Groq service** (no key was available). The request shape follows Groq's documentation; response handling follows the OpenAI-compatible format. First real use may reveal differences (for example a model that rejects JSON mode).
Coverage: upload rejections (type, magic bytes, empty, oversize, encrypted, scanned, macros, missing body, zip bomb, XML entity attack, corrupt), parser child process (no secrets in its environment, timeout and crash handling), storage key safety, de-duplication, per-user limits, ownership (404 on every route), deletion of rows and files (resume and account), analysis (grounding, downgrade, retry with error feedback, hijacked/extra fields, oversized fields, provider errors, unconfigured AI, rate limit), redaction and delimiter/injection handling, role fit (exact matches, aliases, inferred vs stated, no hiring-probability wording), Groq provider request shape and error mapping (mocked).
Limits: prompt-injection behaviour was tested with scripted fake models only; it shows our validation catches bad output, not that a real model ignores injected instructions. Windows, browsers and large real-world resumes not tested.

## Phase 3 (run by Claude in the Linux sandbox; not on Windows)
| Command | Result |
|---|---|
| `python -m pytest -q` (SQLite) | 65 passed |
| same with `TEST_DATABASE_URL` -> PostgreSQL 16 | 65 passed |
| `ruff check .` | All checks passed |
| `npm run test` / `lint` / `build` / `tsc -b` | 37 passed / clean / ok / clean |
| Live workflow on a fresh PostgreSQL DB (`alembic upgrade head` -> 0002; signup; 403 for non-admin; `make-admin`; `import-seed` 14 created; public list empty; verification refused with 3 reasons; add location + source; verify; public list shows the company) | Worked as designed. **The source was a fake `example.test` URL in a throwaway database. It proves the workflow, not any real company.** |

Phase 3 coverage: access control, CSRF on admin writes, Lahore-only listing (candidate/rejected/stale/forced-verified-without-Lahore/non-Lahore locations excluded), verification requirements, cross-company evidence refusal, reviewer/evidence recording, label/type rules, URL/date validation, freshness relabelling for each source type, stale-check CLI, filters/search/paging, seed guards (names only, idempotent, cannot carry status, re-import cannot change verification), make-admin CLI, admin edits cannot change status.
Web coverage (API mocked): empty/list/filter/error states, source labels and stale warning, admin gating, verify flow, refusal details, details form.
Not verified: browser rendering of directory/admin screens, Windows, behaviour with hundreds of companies.

## Phase 2: API (`apps/api`)
| Command | Result |
|---|---|
| `python -m pytest -q` (SQLite temp file) | 30 passed |
| `TEST_DATABASE_URL=postgresql+psycopg://... python -m pytest -q` (PostgreSQL 16, tables created by Alembic) | 30 passed |
| `ruff check .` | All checks passed (after I raised line length to 140 and excluded generated migrations; 4 import-order findings and 1 `assert` were fixed) |
| `alembic upgrade head`, `downgrade base`, `upgrade head` (SQLite) | Succeeded; tables listed correctly |
| Live smoke test: uvicorn + PostgreSQL; curl `/health`, signup, `/me` | 200 / 201 / 200; cookies were httpOnly |
| Live smoke test through the Vite proxy: `/health`, login, `/me`, POST without CSRF header | 200 / 200 / 200 / 403 `csrf_failed` |

Covered: signup/login/logout/refresh flows, Argon2id storage, case-insensitive duplicate email, validation errors, CSRF (missing and forged), identical login failure for unknown email vs wrong password, login and signup rate limits, expired/forged/`alg:none` tokens, inactive users, refresh rotation, refresh reuse revoking the family, expired refresh, profile/consent updates (and that `role` can't be set), account deletion cascade, audit log holding no email, error shape, no leakage on 500, weak secret rejection, cookie Secure flag by environment, cross-user resource access (404), migrations up/down.

## Phase 1 + 2: Web (`apps/web`)
| Command | Result |
|---|---|
| `npm run test` | 29 passed (17 route renders, 8 auth tests, directory, labels, consent gate). The API client is mocked |
| `npm run lint` | Passed (after removing a stray comment that referenced a rule I don't use) |
| `npm run build` | Passed; main chunk still over 500 kB (warning) |

## Not verified
- Windows. Real browser behaviour (clicking through login, cookies in a browser, layouts, keyboard navigation, contrast).
- The real front-end API client (`api.ts`): tests mock it; only curl exercised the HTTP side.
- Multi-worker or multi-tab behaviour; concurrent refresh from two tabs.
- Security tooling beyond tests: no `pip-audit` was run on Python dependencies; `npm audit` findings from Phase 1 are unchanged.
- A test warning remains: Starlette says TestClient with httpx is deprecated (cosmetic).
