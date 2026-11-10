# PROJECT_CONTEXT.md — InterviewPilot AI

_Last updated: 2026-10-30 (remaining work completed, no Docker)_

## 1. Purpose
AI-powered interview preparation and coding-assessment platform for students, fresh graduates, interns and junior professionals targeting **technology employers with a verified physical presence in Lahore, Pakistan**. Lahore-specific company intelligence is a core requirement, not a filter bolted on later.

## 2. Lahore-only scope (non-negotiable)
- Only companies with a *verified* Lahore office/business presence appear as target companies.
- Remote-only or overseas employers with no Lahore office are excluded.
- Named research candidates (Arbisoft, Systems Limited, NETSOL, Tkxel, 10Pearls, CureMD, Folio3, Devsinc, PureLogics, Nextbridge, NorthBay, Conrad Labs, Mindstorm Studios, Xeven Solutions, ...) are **candidates, not verified entries**. None has been verified yet.
- Enforcement is layered: DB constraint (verified Lahore location required for `verified` status), API validation, UI filters, tests. See `COMPANY_DATA_POLICY.md`.

## 3. Evidence labels (used everywhere company content is shown)
1. `official_verified` — supported by an official company source.
2. `public_candidate_report` — public candidate experience; may be outdated.
3. `ai_generated_practice` — generated for practice; never presented as an actual company question.
4. `unverified_or_outdated` — insufficient/stale/conflicting evidence.

## 4. Planned stack (all PROPOSED until Phase 0 is approved)
- Frontend: React, TypeScript, Vite, Tailwind CSS, shadcn/ui (Radix), React Router, TanStack Query, Monaco Editor, Recharts.
- Backend: Python, FastAPI, Pydantic, SQLAlchemy, Alembic, PostgreSQL (SQLite only as a test/dev fallback).
- AI: Groq (initial LLM provider) behind a provider interface; LangChain for integrations; LangGraph for stateful workflows.
- Research: Tavily (initial) behind a `ResearchProvider` interface.
- Code execution: separate isolated runner service. **Isolation approach is BLOCKED pending a user decision (ADR-006).**
- Voice: browser Web Speech API + text fallback behind a `SpeechProvider` interface.
- No Docker/Kubernetes/paid hosting unless explicitly approved (ADR-006 asks for a sandbox-only Docker decision).

## 5. Current status (2026-10-30)
Everything planned is built. The project is a **local MVP, not production-ready, and not yet verified on the user's machine** (see `KNOWN_ISSUES.md`, `HANDOVER.md`).
- **Built and tested on Linux:** UI and design system; authentication, CSRF, ownership, change password and an admin reset command; Lahore company directory with admin verification, evidence labels and 14 seeded *candidate* names; resume upload, parsing, analysis and role fit; admin-run company research with approval; AI-written practice assessments with objective MCQ scoring; **coding practice with real sandboxed execution** (bubblewrap, no Docker; Linux or Windows via WSL2; ADR-058); voice and text interviews with consent, retention controls and feedback; scored reports (rubric `report-1`) with 7- and 30-day plans, comparison and progress; security hardening and audits.
- **Tests:** backend 577, all passing on PostgreSQL 16 as a normal user with the live runner (499 passed and 78 skipped where bubblewrap is unavailable, such as plain Windows); frontend 137; lint, typecheck and build clean; migrations 0001 to 0008 verified; the delivered archive is extracted fresh and installed from scratch in verification.
- **Not verified by anyone:** Windows, WSL2, a real browser or microphone, the real Groq and Tavily services.
- **Known limits:** coding needs WSL2 for real execution (otherwise "Not run"); no company is verified until an admin does it; no email, so password reset is a command; no deployment configuration; short answers and complexity analysis are not scored.
- **Awaiting the user:** running `SETUP_WINDOWS.md` on Windows with real keys and reporting what fails.

## 6. Key constraints
- User works in normal Claude chat (not Claude Code), on local Windows + PowerShell. Claude cannot touch the user's disk; files are delivered as downloads/archives and copied by the user.
- One phase at a time; user approval required between phases.
- No fabricated company data, interview rounds, vacancies, salaries, contacts, or test results.
- Never run untrusted code in the FastAPI process.
- Scores are preparation indicators, not hiring predictions.

## 7. Important decisions
See `DECISIONS.md` (ADR-001 to ADR-011, all Proposed; ADR-006 blocked).
