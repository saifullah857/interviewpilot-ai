# FILE_MANIFEST.md
_Phase 0 snapshot — only documentation and config placeholders exist._

```
interviewpilot-ai/
  README.md                    Project intro and Phase 0 note
  .gitignore                   Excludes secrets, venvs, node_modules, uploads, DB files
  docs/
    PROJECT_CONTEXT.md         Purpose, scope, stack, status
    ARCHITECTURE.md            Architecture, agents, data model, security, folders
    IMPLEMENTATION_PLAN.md     Phases, dependencies, acceptance criteria
    TASKS.md                   Task board
    CHANGELOG.md               Per-phase changes
    FILE_MANIFEST.md           This file
    DECISIONS.md               ADRs
    NEXT_SESSION.md            Resume-here state, commands, open decisions
    TEST_REPORT.md             Executed vs proposed tests
    API_CONTRACTS.md           Proposed endpoint and provider contracts
    COMPANY_DATA_POLICY.md     Lahore eligibility, verification, freshness
    RISKS_AND_COSTS.md         Risks, API costs, alternatives
```
Created this phase: all of the above. Changed: none. Removed: none.

## Phase 1 additions (`apps/web/`)
```
apps/web/
  package.json, package-lock.json   Dependencies and scripts (dev, build, lint, test)
  vite.config.ts                    Vite + Vitest config
  tsconfig.json                     TypeScript config (strict)
  tailwind.config.js, postcss.config.js   Design tokens (brand, ink, deck, status colours, fonts)
  eslint.config.js                  Lint rules
  index.html, public/favicon.svg
  src/
    main.tsx, App.tsx               Entry and routes (Coding page lazy-loaded)
    index.css                       Tailwind layers, fonts, focus ring, reduced-motion rules
    layouts/AppShell.tsx            Sidebar/mobile nav, skip link, logo
    layouts/PublicLayout.tsx        Landing/auth layout
    components/ui.tsx               Shared components and state screens
    lib/evidence.ts                 Four evidence labels and descriptions
    data/sample.ts                  ALL sample data (fictional companies; not verified)
    pages/                          Landing, Auth, Dashboard, Companies, CompanyDetail, Resume,
                                    Assessment (setup/instructions/technical), Coding, Voice,
                                    Results, History, Settings, NotFound
    test/setup.ts, App.test.tsx     Test setup and 21 tests
```
Changed: docs listed in CHANGELOG. Removed: none.

## Phase 2 additions
- Removed: root `.env.example` (replaced by `apps/api/.env.example` and `apps/web/.env.example`).
- Added `docs/SETUP_WINDOWS.md`.
```
apps/api/
  pyproject.toml, requirements.txt, requirements-dev.txt, .env.example, alembic.ini
  alembic/env.py, script.py.mako, versions/0001_users_auth_audit.py
  app/main.py                    App factory, CSRF middleware, CORS, /health
  app/core/{config,db,errors,security,rate_limit,ownership}.py
  app/models/{user,audit}.py     users, user_profiles, refresh_tokens, audit_events
  app/auth/{routes,service,deps,cookies,schemas}.py
  app/users/{routes,mapping}.py  /me endpoints
  tests/{conftest,test_auth,test_ownership,test_migrations}.py
apps/web/src/lib/{api.ts,auth.tsx}   API client, auth context and route guard
apps/web/.env.example
```
Changed: apps/web (App.tsx, Auth.tsx, Settings.tsx, AppShell.tsx, vite.config.ts, App.test.tsx).

## Phase 3 additions
```
data/company_seed/lahore_candidates.json     14 candidate names, no facts
apps/api/alembic/versions/0002_companies_directory.py
apps/api/app/models/company.py               Company, CompanyLocation, ResearchSource, CompanyVerificationRecord
apps/api/app/companies/{schemas,service,mapping,routes,freshness,seed}.py
apps/api/app/cli.py                          import-seed, make-admin, stale-check
apps/api/tests/test_companies.py
apps/web/src/pages/Admin.tsx                 Company review screen (admin only)
```
Changed: apps/api/app/main.py, models/__init__.py; apps/web: lib/api.ts, lib/auth.tsx (RequireAdmin), App.tsx, layouts/AppShell.tsx, pages/{Companies,CompanyDetail,Assessment,Dashboard}.tsx, data/sample.ts, App.test.tsx.

## Phase 4 additions
```
data/roles/roles.json                         General role skill lists (not company-specific)
apps/api/alembic/versions/0003_resumes.py
apps/api/app/models/resume.py                 Resume, ResumeVersion
apps/api/app/llm/{base,structured,groq,fake,factory}.py
apps/api/app/storage/{base,local}.py
apps/api/app/resumes/{routes,files,parse_worker,text,schemas,analyst,roles}.py
apps/api/tests/{factories,test_resumes}.py
apps/web/src/pages/Resume.tsx                 Rewritten; Dashboard.tsx, lib/api.ts, App.test.tsx updated
```
Changed: core/config.py, core/rate_limit.py, main.py, users/routes.py, requirements*.txt, .env.example, .gitignore (storage_private/).

## Phase 5 additions
```
apps/api/alembic/versions/0004_company_research.py
apps/api/app/research/{provider,classify,schemas,workflow,service,routes}.py
apps/api/tests/test_research.py
```
Changed: models/company.py (ResearchRun, ResearchFinding; source columns), companies/{service,schemas,mapping}.py, resumes/{routes,text,analyst}.py, core/{config,rate_limit}.py, main.py, requirements.txt (langgraph), .env.example; web: lib/api.ts, pages/{Admin,CompanyDetail,Resume}.tsx, App.test.tsx.

## Phase 6 additions
```
apps/api/alembic/versions/0005_assessments.py
apps/api/app/models/assessment.py
apps/api/app/assessments/{schemas,validate,context,workflow,service,routes}.py
apps/api/tests/{assess_helpers,test_assessments}.py
apps/web/src/pages/{AssessmentPage,AssessmentTake,AssessmentReview}.tsx
```
Changed: web pages/Assessment.tsx (setup, rewritten), History.tsx, Dashboard.tsx, App.tsx, lib/api.ts, data/sample.ts (sample questions/history removed), App.test.tsx; api core/{config,rate_limit}.py, main.py (PUT allowed), models/__init__.py, tests/conftest.py.

## Phase 7 additions
```
docs/SANDBOX_DESIGN.md
scripts/build_coding_problems.py                problem definitions + reference solutions; writes data/coding/problems.json
data/coding/problems.json                       10 practice problems (hidden tests included; server-side only)
services/sandbox-runner/                        separate service (own README, requirements, .env.example)
  runner/{contract,harness,app,main}.py, runner/backends/{base,mock}.py
apps/api/alembic/versions/0006_coding.py
apps/api/app/models/coding.py
apps/api/app/coding/{schemas,service,routes,problems,runner_client,runner_contract}.py
apps/api/tests/{coding_helpers,test_coding}.py
apps/api/tests/runner/{conftest,helpers,mutants,test_harness,test_problem_bank,test_runner_service,test_conformance_hostile}.py
apps/web/src/pages/{CodingList,CodingSession,CodingReview}.tsx, components/CodingResults.tsx, lib/text.tsx
```
Removed: apps/web/src/pages/Coding.tsx (sample page). Changed: web lib/api.ts, App.tsx, layouts/AppShell.tsx, pages/AssessmentReview.tsx, App.test.tsx; api core/{config,rate_limit}.py, main.py, cli.py, models/__init__.py, tests/conftest.py, .env.example.

## Phase 8 additions
```
apps/api/alembic/versions/0007_interviews.py
apps/api/app/models/interview.py
apps/api/app/interviews/{schemas,workflow,evaluate,service,routes}.py
apps/api/tests/{interview_helpers,test_interviews}.py
apps/web/src/pages/{InterviewRoom,InterviewReview}.tsx   (Voice.tsx rewritten)
apps/web/src/components/VoiceOrb.tsx, apps/web/src/lib/speech.ts
```
Changed: api models/__init__.py, core/{config,rate_limit}.py, main.py, pyproject.toml, tests/{conftest,test_migrations,test_auth}.py; web lib/api.ts, App.tsx, App.test.tsx; docs.

## Phase 9 additions
```
apps/api/alembic/versions/0008_reports.py
apps/api/app/models/report.py
apps/api/app/reports/{rubric,compute,roadmap,schemas,service,routes}.py
apps/api/tests/test_reports.py
apps/web/src/pages/ReportView.tsx   (Results.tsx and Dashboard.tsx rewritten)
docs/SCORING_RUBRICS.md
```
Removed: `apps/web/src/data/sample.ts`. Changed: api models/__init__.py, core/{config,rate_limit}.py, main.py, assessments/service.py (one note), pyproject.toml, tests/{conftest,test_migrations,test_assessments}.py; web lib/api.ts, App.tsx, App.test.tsx, layouts/AppShell.tsx; docs.

## Phase 10 additions
```
apps/api/app/core/nul_guard.py
apps/api/tests/{test_security_sweep,test_journey}.py
docs/SECURITY_REVIEW.md
```
Changed: api main.py (security headers, NUL guard), core/errors.py (DataError handler), requirements.txt (pypdf), tests/test_{coding,security_sweep}.py; web package.json and package-lock.json (dompurify override); docs.

## Final inventory (generated from the delivered tree, 2026-10-27)
| Area | Path | Files | Lines |
|---|---|---|---|
| API application code | `apps/api/app` | 87 | 7,819 |
| API tests | `apps/api/tests` | 26 | 5,731 |
| API migrations | `apps/api/alembic/versions` | 8 | 743 |
| Web application code | `apps/web/src` | 37 | 4,338 |
| Sandbox runner service (development mock + contract) | `services/sandbox-runner` | 8 | 296 |
| Data (company seed names, role catalog, coding problem bank) | `data` | 3 | 108,555 |
| Scripts | `scripts` | 1 | 197 |
| Documentation | `docs` | 16 | 1,588 |

API packages: assessments, auth, coding, companies, core, interviews, llm, models, reports, research, resumes, storage, users
Web pages: Admin, Assessment, AssessmentPage, AssessmentReview, AssessmentTake, Auth, CodingList, CodingReview, CodingSession, Companies, CompanyDetail, Dashboard, History, InterviewReview, InterviewRoom, Landing, NotFound, ReportView, Results, Resume, Settings, Voice
Migrations: 0001, 0002, 0003, 0004, 0005, 0006, 0007, 0008

Totals: 71 API endpoints, 21 database tables, 501 backend tests (489 run + 12 skipped), 133 frontend tests.
Top level: `README.md`, `apps/`, `services/`, `data/`, `scripts/`, `docs/`, `.gitignore`. Documents (18): API_CONTRACTS, ARCHITECTURE, CHANGELOG, COMPANY_DATA_POLICY, DECISIONS, FILE_MANIFEST, HANDOVER, IMPLEMENTATION_PLAN, KNOWN_ISSUES, NEXT_SESSION, PROJECT_CONTEXT, RISKS_AND_COSTS, SANDBOX_DESIGN, SCORING_RUBRICS, SECURITY_REVIEW, SETUP_WINDOWS, TASKS, TEST_REPORT.
Excluded from the archive on purpose: `.env` files, uploaded resumes and `storage_private/`, databases, transcripts, `node_modules`, virtual environments, build output, caches. A secret scan of the archive found nothing; `.env.example` files hold placeholders only.
Phase 11 changed **no application code**: only documents (`HANDOVER.md`, `KNOWN_ISSUES.md` new; others updated) and one wrong variable name in a troubleshooting table.

## Phase 12 additions
```
services/sandbox-runner/runner/backends/bwrap.py    (real sandbox backend)
services/sandbox-runner/.env.example, README.md     (rewritten)
scripts/start-runner.sh, .gitattributes
apps/api/tests/runner/test_bwrap_backend.py
apps/api/tests/test_real_server.py    (tests over a real socket)
```
Changed: runner `harness.py` (sandbox mode), `app.py` (non-blocking runs, backend selection); api `auth/{schemas,service}.py`, `users/routes.py`, `cli.py`, `.env.example`; `tests/test_auth.py`, `tests/test_coding.py` (earlier); web `lib/api.ts`, `pages/Settings.tsx`, `App.test.tsx`; docs (`SETUP_WINDOWS.md` rewritten).

## Final inventory (regenerated 2026-10-30)
| Area | Path | Files | Lines |
|---|---|---|---|
| API application code | `apps/api/app` | 87 | 7,885 |
| API tests | `apps/api/tests` | 27 | 6,112 |
| API migrations | `apps/api/alembic/versions` | 8 | 743 |
| Web application code | `apps/web/src` | 37 | 4,413 |
| Code runner service (real bubblewrap backend + mock) | `services/sandbox-runner` | 9 | 588 |
| Scripts | `scripts` | 2 | 243 |
| Documentation | `docs` | 18 | 1,792 |

Totals: 72 API endpoints, 21 database tables, 8 migrations, 577 backend tests (all pass on PostgreSQL 16 with the live runner), 137 frontend tests. Documents: 18 in `docs/` plus `README.md` and the runner README.

## Added 2026-11-02
- `START.bat`: one-click start (runner, API, web). `scripts/prepare_env.py` (sets RUNNER_* in .env), `scripts/run_runner.py` (starts the runner).
- `services/sandbox-runner/runner/backends/local.py`: cross-platform local process backend; `harness.py` gained the restricted-import mode.
- `apps/api/app/assessments/bank.py`: built-in practice question bank (fallback).
- `apps/api/app/discover/`: role/company recommendations and user-run research API. `apps/api/app/research/auto.py`: domain discovery and automatic Lahore confirmation.
- `data/company_seed/lahore_profiles.json`: rough focus families for candidates (not verified facts).
- Tests: `tests/test_discover.py`, `tests/runner/test_local_backend.py`.
