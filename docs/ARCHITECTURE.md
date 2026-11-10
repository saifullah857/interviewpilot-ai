# ARCHITECTURE.md — Phase 0 Proposal (not yet approved)

## 1. System overview
```
Browser (React SPA)
  |  HTTPS/JSON (cookie auth)         Web Speech API (STT/TTS, optional)
  v
FastAPI backend (apps/api)  ------------------------------+
  | routers -> services -> repositories (SQLAlchemy)      |
  |                                                       |
  +-- LangGraph workflows (resume, research, assessment,  |
  |   interview, report) --> LLMProvider (Groq)           |
  +-- ResearchProvider (Tavily) -- untrusted web content  |
  +-- StorageProvider (private local dir, opaque IDs)     |
  +-- SandboxClient --(signed HTTP, network-isolated)--> Runner service (services/sandbox-runner)
  v
PostgreSQL
```
Modular monolith for the main backend (one deployable, strict module boundaries). The code runner is the only separate service because it must be isolated.

## 2. Backend modules (apps/api/app)
`auth`, `users`, `companies` (directory + verification), `research` (agent + evidence), `resumes`, `roles` (role catalog + matching), `assessments`, `coding`, `interviews`, `evaluation` (scoring + reports), `llm` (provider abstraction), `storage`, `core` (config, security, errors, rate limiting, logging), `audit`.
Rule: routers never call the LLM or DB directly; services own business logic; agents are called only from services.

## 3. Agents and workflows
Agents are LangGraph graphs only where state/branching justifies it; otherwise plain service functions with structured output. All LLM outputs are Pydantic-validated with a max of 2 retries, then a typed failure (never silent fallback to fabricated content).

| Agent | Type | Input -> Output | Notes |
|---|---|---|---|
| Resume Analyst | Graph: parse -> extract -> validate -> gap-hints | PDF/DOCX text -> `ParsedResume` (facts flagged `stated`, inferences flagged `inferred`) | Resume text is untrusted data (prompt-injection safe prompt framing; no tools). |
| Company Research | Graph: validate-company -> search -> fetch -> extract -> classify -> freshness-check -> persist | Company + role -> `ResearchBundle` of `EvidenceItem`s with URL, type, retrieved_at, label | Only tool access: search/fetch via ResearchProvider with domain/size/timeouts. Web text never enters system prompt. |
| Role Matching | Service (LLM + deterministic skill normalizer) | ParsedResume + RoleRequirements (+ evidence) -> `FitAnalysis` | Deterministic skill taxonomy match first; LLM explains. Not a hire probability. |
| Assessment Generator | Graph: plan -> generate batches -> validate -> dedupe -> label | Resume, role, evidence, history -> `Assessment` (20–30 Qs) | Validators: schema, duplicate check, MCQ key re-verification by second pass, ambiguity check on coding tasks. Every question carries `evidence_label`. |
| Coding Evaluation | Service (no LLM for correctness) | Code + problem id -> runner result | LLM may add *quality/complexity commentary* only, clearly separate from test results. |
| Voice Interview | Graph state machine: consent -> intro -> question -> listen -> follow-up/branch -> wrap-up -> evaluate | Resume, role, evidence -> turns + `InterviewEvaluation` | Question-repeat guard; transcript stored only with consent. |
| Evaluation & Report | Service | Results -> `Report` with versioned rubric | Objective and subjective scores stored separately. |

## 4. Company verification and evidence flow
1. Candidate company created from seed file/admin import with status `candidate`.
2. Research agent (or human) collects Lahore-presence evidence (official site contact/careers pages, etc.).
3. Verification needs the criteria in `COMPANY_DATA_POLICY.md` **and a human review step** (the user) before `verified_lahore`.
4. All displayed company facts link to `EvidenceItem` rows (URL, source type, retrieved_at, label, content hash).
5. Freshness job flags stale evidence -> label `unverified_or_outdated`.
6. If research is unavailable, UI shows "Live verification unavailable" with last verified data, never invented data.

## 5. Data model proposal (PostgreSQL; all tables have id (UUID), created_at, updated_at)
| Entity | Key fields / constraints |
|---|---|
| users | email (unique, citext), password_hash (Argon2id), is_active, role (`user`/`admin`) |
| user_profiles | user_id FK, display_name, education_level, target_roles[], consent_flags (voice_transcript, analytics) |
| resumes | user_id FK, storage_key, original_filename, mime, size, sha256, status, deleted_at |
| resume_versions | resume_id FK, parsed_json (validated), schema_version, model/provider |
| companies | slug (unique), name, website, careers_url, description, tech_focus[], verification_status (`candidate`/`pending_review`/`verified_lahore`/`stale`/`rejected`), last_verified_at |
| company_locations | company_id FK, locality (enum-ish), address, is_lahore (bool), verified_at. CHECK: `verified_lahore` company needs >=1 location with is_lahore=true (enforced in service + test) |
| company_verification_records | company_id FK, reviewer_id, decision, notes, evidence_ids[] |
| research_sources | company_id FK, url, source_type, label, retrieved_at, content_hash, excerpt, status |
| job_postings | company_id FK, role_id FK nullable, title, url, requirements_json, posted_at (if known), last_seen_at, source_id FK |
| roles / role_requirements | canonical role catalog, normalized skills, weight |
| assessment_sessions | user_id, resume_version_id, role_id, company_id nullable (null = general role prep, labelled), status, timer fields, assessment_version, rubric_version |
| questions / answer_options | session_id, type, prompt, correct_key (never sent to client before submit), evidence_label, source_ids[] |
| answers | question_id, user_id, response, graded_by (`auto`/`llm`), score |
| coding_problems | title, statement, constraints, visible_tests, hidden_tests (server only), language_support |
| coding_submissions / test_results | user_id, problem_id, language, code, status, per-test pass/fail, runtime_ms, runner_version |
| interview_sessions / interview_turns | user_id, consent_at, status, transcript (nullable unless consented), evaluation_json |
| scoring_rubrics | name, version, criteria_json |
| evaluation_reports | session_id, scores (objective/subjective separate), rubric_version, model/provider, generated_at |
| skill_gaps / learning_recommendations | report_id, skill, severity, evidence, plan items (7/30-day) |
| audit_events | actor_id, action, entity, entity_id, metadata, at |

Ownership: every user-scoped query goes through a repository method that requires `user_id`; tests assert 404 on cross-user access.

## 6. API boundaries
REST under `/api/v1`, JSON, Pydantic schemas, uniform error body `{error:{code,message,details?}}`. Groups: `/auth`, `/me`, `/companies`, `/roles`, `/resumes`, `/research`, `/assessments`, `/coding`, `/interviews`, `/reports`, `/health`. Long operations (parse, research, generate) are jobs with status polling (BackgroundTasks first; no Celery/Redis in MVP). Detail in `API_CONTRACTS.md`.

## 7. Security model
- Auth: Argon2id; short-lived access token + rotating refresh token in httpOnly, Secure, SameSite cookies; CSRF protection on state-changing calls; login rate limiting.
- Authorization: ownership enforced in repository layer; admin role only for directory management.
- Uploads: size cap, extension + magic-byte check, parse in a restricted worker function with timeout, no macro execution, stored outside any public dir under random IDs, served only via authorized endpoint.
- Prompt injection: external/resume text is wrapped as delimited data, agents get no tools beyond search/fetch, outputs schema-validated, URLs from outputs re-validated against recorded sources.
- Code execution: runner is network-disabled, resource-capped, ephemeral, authenticated with a shared secret; hidden tests never leave the server. (Approach pending ADR-006.)
- Secrets only via environment variables; `.env` git-ignored; `.env.example` placeholders only.
- Privacy: explicit consent before storing voice transcripts; delete-my-data endpoint; retention settings; honest AI-limitations notice. Integrity monitoring (if any) is opt-in, best-effort, never presented as proof.

## 8. Scoring rubric (draft; finalized and versioned in Phase 9)
Separate scores, each 0–100 with criteria listed in the report: Resume-to-role fit; Technical knowledge (MCQ/short answer); Coding correctness (tests passed — objective); Problem-solving/complexity (LLM-assessed, labelled subjective); Voice interview (technical correctness, reasoning, clarity, evidence); Communication; Overall preparation progress (trend across attempts, not a hire probability). Objective and subjective results are stored in separate fields.

## 9. Proposed folder structure
```
interviewpilot-ai/
  README.md  .gitignore  .env.example
  docs/                     (project documents; this folder)
  apps/
    web/                    (Vite + React + TS)
      src/{app,components,features,pages,lib,styles}
    api/
      app/{core,auth,users,companies,research,resumes,roles,assessments,coding,interviews,evaluation,llm,storage,audit}
      alembic/  tests/  pyproject.toml
  services/
    sandbox-runner/         (isolated executor; separate process/service)
  data/
    company_seed/           (candidate companies as JSON; labelled seed data)
  scripts/                  (PowerShell helpers: setup, backup, test)
```

## 10. Out of scope for MVP
Multi-language execution beyond Python, facial/emotion analysis, employer-side features, payments, public deployment, mobile apps.
