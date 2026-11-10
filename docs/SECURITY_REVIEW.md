# SECURITY_REVIEW.md — Phase 10 (2026-10-24), updated for the code runner in Phase 12 (2026-10-30)
_What was checked, how, and what is still open. "Evidence" names an automated test or command that was actually run in Claude's Linux sandbox. Nothing here was run on your Windows machine, against the real Groq or Tavily services, or with a real code runner._

## Result in one paragraph
Two real problems were found and fixed (known-vulnerable `pypdf`; a PostgreSQL-only server error on NUL characters) and one gap was closed (no security headers). Everything else reviewed held up under automated checks. **Phase 12 update:** a real sandboxed code runner now exists (bubblewrap, no Docker) and was tested against hostile programs on Linux; see the new section "Code runner" below. **Still not reviewed or not possible here:** a real browser, Windows/WSL2 itself, and the real AI providers. The product must not be described as production-ready.

## Findings and fixes
| # | Finding | Severity | Fix | Evidence |
|---|---|---|---|---|
| 1 | `pypdf` 6.20.1 had 7 published vulnerabilities; it parses untrusted uploads (inside the child process) | High | pinned `pypdf==6.21.2` | `pip-audit -r requirements.txt` before: 7 findings; after: none. `tests/test_resumes.py` still passes |
| 2 | A NUL character in a path, query or JSON text caused an unhandled database error (HTTP 500) on **PostgreSQL**; SQLite stored it silently, so earlier phases never saw it | Medium (no data leak, but a hostile request could trigger server errors and the two databases behaved differently) | `app/core/nul_guard.py` rejects NUL at the edge (400 for path/query, 422 for JSON, 413 over 1 MiB); `DataError` handler returns 422 as a safety net | `test_hostile_requests_never_cause_a_500_or_leak_internals`, `test_nul_*` (24 sweep tests) on both databases |
| 3 | API responses had no security headers | Low | middleware adds `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, a restrictive CSP, `Cache-Control: no-store` under `/api/`, HSTS in production | `test_every_response_carries_security_headers` |
| 4 | `dompurify` (inside Monaco) had published advisories (flagged critical by `npm audit`) | Medium (used by the editor's own UI, not for your content) | `overrides: dompurify 3.4.17` | `npm audit --omit=dev`: 0 vulnerabilities |

## Accepted, still open
- **Tailwind v3 build tooling**: `npm audit` reports 3 moderate findings (`postcss-selector-parser` CPU exhaustion on hostile CSS at build time). It is not shipped to users; fixing it needs a Tailwind major upgrade, which risks the design system. Revisit before deployment.
- **The code runner (Phase 12)**: now real on Linux and WSL2, but it has only been tested on a Linux machine, never on WSL2. Residual risks are listed in the "Code runner" section. Without WSL2 (plain Windows) coding stays on the mock and shows "Not run".
- **Rate limits are in memory**: correct for one local process; they reset on restart and are not shared across workers. A shared store is needed before running more than one process.
- **Secrets**: the Groq/Tavily/runner keys live in `.env` on your machine. Anyone with access to that file has the keys.
- **Voice**: when a browser's speech recognition is used, some browsers send audio to the browser vendor. The product says so; it cannot control it.
- **No Playwright / real-browser test** (browser downloads are not available in my sandbox). The journey is tested at the API level and the pages with component tests; real-browser behaviour (microphone prompts, speech, reduced motion, Monaco) is unverified.

## Areas reviewed
| Area | Controls found | Evidence |
|---|---|---|
| Authentication | Hashed passwords, short-lived access cookie, rotating refresh token with reuse detection, expired/forged tokens rejected, login does not reveal whether an email exists | `test_auth.py`; `test_login_errors_do_not_reveal_whether_an_email_exists`; `test_passwords_are_hashed_and_no_user_response_contains_a_hash` |
| Authorisation | Every route requires login except 5 deliberate ones (72 routes now); admin routes refuse members; ownership checked per resource | `test_only_the_deliberately_open_routes_answer_without_login` (all 71 routes), `test_every_unauthenticated_denial_is_a_clean_401_with_no_detail`, `test_admin_routes_refuse_ordinary_members`, per-feature ownership tests, journey cross-user test |
| CSRF | Double-submit token on every state-changing route | `test_every_state_changing_route_needs_the_csrf_token`, `test_a_wrong_csrf_token_is_refused` |
| CORS and cookies | Single configured origin, never `*`; cookies HttpOnly, SameSite=Lax, Secure in production; refresh cookie scoped to `/api/v1/auth` | `test_cors_allows_only_the_configured_origin_and_never_a_wildcard`, `test_session_cookies_are_httponly_samesite_and_secure_when_configured` |
| Error handling | Unexpected errors return a generic body; fuzzing over 1,000 hostile requests found no 500s (after fix 2) and no stack traces, paths, library names or key canaries | `test_an_unexpected_exception_returns_a_generic_500_without_the_message`, `test_hostile_requests_never_cause_a_500_or_leak_internals` |
| Production mode | API docs hidden; weak or default secret refused; HSTS | `test_production_hides_the_docs_and_refuses_weak_secrets` |
| Secrets | No key-shaped strings in the repository; `.env` ignored; `.env.example` placeholders only; no `.env` inside the project tree | `test_no_real_looking_secrets_are_committed`, `test_env_files_are_ignored_and_the_example_holds_placeholders_only`; the archive is built without `.env` |
| File handling | Type, size and content validation; hostile filenames neutralised; macros, zip bombs, XML entity attacks, encrypted PDFs refused; parser in a child process without secrets; private storage with random names | `tests/test_resumes.py` (see names in file) |
| Prompt injection | Resume text, web research, interview answers and report plans are delimited as untrusted data; delimiter escape neutralised; AI output validated (unknown fields, links, markup, instruction-like text rejected) and nothing the AI writes can change a score | per-feature tests in `test_resumes`, `test_assessments`, `test_research`, `test_interviews`, `test_reports` (tampered plans) |
| Code execution | No dynamic execution anywhere in the API process; the only child process is the resume parser (fixed arguments, no shell); submitted code only goes to a runner client | `test_the_main_process_has_no_dynamic_code_execution`, `test_user_submitted_code_is_never_executed_by_the_api_process` |
| Privacy and deletion | Consent required before an interview; transcripts kept only if chosen, otherwise removed after feedback or 24 h; account deletion removes every user-owned row, child rows and the uploaded file | `test_interviews.py`; journey test (all tables with a `user_id`, plus child tables, plus stored files) |
| Lahore-only scope | Unverified or candidate companies are invisible in the directory and cannot be chosen for fit, assessments, interviews or reports; only approved evidence is cited | journey test, `test_companies.py`, `test_research.py`, `test_reports.py` |
| Dependencies | Python and npm audited | `pip-audit`, `npm audit` (see findings) |
| Migrations | 0001 to 0008 apply, reverse and re-apply on PostgreSQL 16; models match migrations (`alembic check`: no drift) | commands in TEST_REPORT.md |

## Recommended before any real deployment
1. Run the runner and its 80 sandbox tests inside WSL2 on your machine; have someone independent review `docs/SANDBOX_DESIGN.md` section 7 before the runner ever executes anyone else's code.
2. Move rate limits to a shared store.
3. Upgrade Tailwind (or accept the build-tool advisory knowingly).
4. Run a real-browser journey (Playwright) on your machine, including microphone denial and Chrome/Edge/Firefox.
5. Rotate any API key that was ever pasted into a chat, file or screenshot.
6. Add a privacy policy page that matches the in-product notices, and a data-retention schedule you are willing to keep.

## Code runner (Phase 12, 2026-10-30)
**What was tested, on Linux only:** 68 backend tests (hostile programs, limits, leftovers, the whole problem bank under real execution) plus the 12-program conformance suite against the live service, run as an unprivileged user. Result: all passed, and no processes or temp folders were left behind.
**Problems found by testing and fixed**
| # | Finding | Fix |
|---|---|---|
| R1 | **A fork bomb was not contained when the runner ran as root**: Linux exempts root-owned processes from the process-count limit, and the machine ran out of memory (the kernel killed the test process). As an ordinary user the same program is capped at 14 processes. | The runner **refuses to start as root**; the tests skip as root. |
| R2 | The first design compared answers inside the same process as the student's code, where hostile code could tamper with the verdict or read hidden expected answers. | Expected answers never enter the sandbox; the trusted runner compares; a reported "passed" is never accepted from inside. Tested with a forged reply. |
| R3 | The runner ran inside a blocking handler, so `/health` froze during a run. | Runs happen off the event loop, at most 2 at a time; tested. |
| R4 | A returned value cap (64 KB) wrongly failed a correct solution on the largest hidden test (about 69,000 characters). Found only because the whole bank was re-validated under real execution. | Cap raised to 150,000 characters; tests for large correct and absurd answers. |
| R6 | Not a runner flaw but found while running the real servers together: every "204 No Content" response carried a stray `null` body, so a real server reset the connection after account deletion, logout, password change and the deletes. In-process tests could not see it. | Body-less responses; `tests/test_real_server.py` over a real socket plus a static guard. |
| R5 | A startup check flagged `PWD` in the environment. | `PWD` is set by the sandbox tool itself and holds nothing secret; allowed explicitly. |
**Controls:** per-test fresh sandbox; no network, no host files, empty environment, read-only `/usr`, private `/tmp`; no capabilities, no nested user namespaces, uid 65534; limits for memory, CPU, file size, open files and **16 processes**; an outside wall-clock kill (the program's own alarm can be ignored); results re-validated and clipped; startup self-check of nine properties that **fails closed**; HMAC-signed requests.
**Residual risks (unchanged by testing):** a kernel vulnerability could escape any namespace sandbox; there is no seccomp filter; worst-case memory of one run is processes times the per-process limit; a program can forge the reported output of tests whose answers it already knows (visible ones) but not hidden ones; repeated submissions can probe hidden answers one guess at a time (rate-limited). **Not reviewed for running other people's code on a public server.**
