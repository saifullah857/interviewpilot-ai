# KNOWN_ISSUES.md — final delivery (updated 2026-10-30)
_Everything below is true of the delivered code. Read the first section first: it is the one thing that stands between "built and tested in a Linux build environment" and "works on your machine"._

## The main open item: nothing has been verified by you
| # | What | Why it matters | What to do |
|---|---|---|---|
| V1 | **The whole project has never been run on your Windows machine.** All tests ran on Linux (SQLite and PostgreSQL 16) with scripted AI doubles. | A Windows-specific problem (paths, PowerShell, the PDF/DOCX parser's child process, PostgreSQL service names) would only show up when you run it. | Follow `SETUP_WINDOWS.md` steps 1 to 7 and 10, and send me the exact text of anything that fails. |
| V2 | **The code runner has never been run on WSL2.** It was built and tested on a Linux machine as an ordinary user: 68 sandbox tests, the 12-program hostile suite, the whole problem bank, and an end-to-end run through the API. | WSL2's kernel or Ubuntu version could block unprivileged user namespaces. If so the runner refuses to start (it never runs code unprotected) and coding stays on "Not run". | `SETUP_WINDOWS.md` step 8, then step 12 (the sandbox tests inside WSL). |
| V3 | **The real AI and search services have never been called.** Groq (resume analysis, questions, interviewer, feedback, plan wording) and Tavily (company research) were only tested through scripted doubles. A real browser, microphone and Monaco were never opened by anyone. | Quality, cost, rate limits and model behaviour are unknown until you try. | Add your keys (step 7) and do the walkthrough (step 10). |

## Limits you should know about
| # | Issue | Detail |
|---|---|---|
| L1 | **Real code execution needs WSL2.** | Without it (plain Windows) coding works as a practice editor but nothing is run and the score is "Not run". Python only. |
| L2 | **The sandbox protects a single-user practice tool, not a public server.** | A Linux kernel vulnerability could escape any namespace sandbox; there is no seccomp filter; a hostile run can use a lot of memory for its few seconds; a program can fake its own reported output for tests whose answers it already knows (the visible ones) but cannot see hidden answers. Details: `SANDBOX_DESIGN.md` section 7, `SECURITY_REVIEW.md`. It must run as a normal user, never root (it refuses). |
| L3 | **No company is verified out of the box.** | 14 candidate names are seeded; every one stays hidden until an admin adds official Lahore evidence and verifies it (`SETUP_WINDOWS.md` step 9). Until then the product works as general role practice. |
| L4 | Company data goes stale. | Re-check about every 180 days (`python -m app.cli stale-check` hides overdue ones). No scheduled job. |
| L5 | No email service, so no emailed password reset and no email verification. | Logged-in users change their password in Settings; an admin runs `python -m app.cli reset-password <email>`. Anyone can sign up with any email address without proving they own it. |
| L6 | Rate limits are in memory. | Fine for one local process; they reset on restart and are not shared between workers. |
| L7 | Short answers are saved but never scored; complexity analysis is not scored. | Technical knowledge in reports is multiple-choice only. |
| L8 | Subjective scores are AI judgements of text. | Interview scores come from answer text only (no voice, accent, pace or appearance). The overall weights (0.35 / 0.35 / 0.30) are a judgement call. Scores are preparation indicators, not hiring predictions. |
| L9 | Speech input depends on the browser. | Chrome and Edge have it; Firefox does not (typing is used automatically). Some browsers send audio to the browser vendor. Recognition quality for Pakistani English is untested. |
| L10 | Not deployable as delivered. | No deployment configuration (hosting, TLS, backups, monitoring). It is a local MVP. Do not expose it to the internet. |
| L11 | Tailwind v3 build-tool advisory. | `npm audit` lists 3 moderate findings in build tooling (CPU exhaustion on hostile CSS at build time). Not shipped to users; production dependencies show 0 vulnerabilities. Fixing needs a Tailwind major upgrade. |

## Minor
- History page lists assessments only; interviews, coding sessions and reports are listed on their own pages.
- Reports mix whichever results you choose; they do not check the results are close in time. A company report is a snapshot of approved evidence at creation time.
- Idle-interview detection and unkept-transcript purge are lazy (applied when the interview is read), not a background job.
- No PDF or Word export of reports; no OCR for scanned resumes.
- Coding session role matching is loose when a session was built from hand-picked problems.
- Each test starts a fresh sandbox (about 50 to 80 ms), so a long test list adds a second or two.
- The web bundle is larger than 500 kB (Monaco loads only on the coding page).
- Older entries in `CHANGELOG.md` and `TEST_REPORT.md` describe what was true at that time; the current state is in `HANDOVER.md` and `PROJECT_CONTEXT.md`.

## Resolved during the project (for the record)
Vulnerable `pypdf` (7 CVEs); PostgreSQL-only server error on NUL characters; missing security headers; `dompurify` advisory; stale "sample data" labels; misleading plan, short-answer and variable-name notes; **no real code execution** (now bubblewrap, ADR-058); **a fork bomb exhausting memory when run as root** (the runner now refuses root); a size cap that wrongly failed a correct solution; **the 204 responses that made a real server reset the connection** (account deletion, logout, deletes, change password); **no way to change or reset a password** (Settings card and admin command).


## Added 2026-11-02
- **Local runner is not a hardened sandbox.** It limits time, memory and imports and hides secrets, but a determined attacker could escape Python restrictions. Use it only for your own practice on your own machine and never expose port 8100. For anything shared, use the bubblewrap backend (Linux/WSL2).
- **The Windows part of the local runner (Job Object memory/process limits, `taskkill`) was written but could NOT be run here** (tested on Linux only: 14 tests plus all 10 problems through the real signed HTTP service). The wall-clock kill, import allow-list and secret-free environment are the same on both systems. Please run the check in docs/SETUP_WINDOWS.md and report back.
- **Real Groq and Tavily were not called from this build environment.** Retry/fallback logic is tested with fakes only. Free-tier Groq limits (tokens per minute) can still slow generation; the built-in bank covers that.
- **Automatic Lahore confirmation is only as good as the search results**: it requires a page on the company's own (auto-discovered) domain that mentions Lahore. Check the website link on the company page; the UI says it was automatic.
- Bank questions are general (not tailored to the resume) and, like all questions here, are practice, never real company questions.
- Frontend/coding problems are Python-only; Frontend and Mobile roles get Python DSA problems for now.
