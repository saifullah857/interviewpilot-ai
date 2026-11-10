# API_CONTRACTS.md

**Status key:** ✅ implemented and tested in Phase 2 · ⏳ proposed only (later phases).

## Implemented in Phase 2 ✅
Base `/api/v1`. JSON. Errors always `{"error":{"code","message","details?"}}`.

**CSRF:** every POST/PATCH/DELETE needs header `X-CSRF-Token` equal to the `ip_csrf` cookie. Get both from `GET /auth/csrf` (returns `{"csrf_token"}` and sets the cookie). Failure: 403 `csrf_failed`.
**Cookies:** `ip_access` (JWT, 15 min, httpOnly, path `/`), `ip_refresh` (opaque, 14 days, httpOnly, path `/api/v1/auth`, rotated on every use), `ip_csrf` (readable by JS). SameSite=Lax; Secure only when `APP_ENV=production`.

| Endpoint | Auth | Request | Success | Errors |
|---|---|---|---|---|
| GET /health | none | | 200 `{status,database}` | 503 if DB down |
| GET /auth/csrf | none | | 200 `{csrf_token}` | |
| POST /auth/signup | none | `{email, password (8-128), display_name?}` | 201 `Me` + cookies | 409 `email_taken`, 422, 429 |
| POST /auth/login | none | `{email, password}` | 200 `Me` + cookies | 401 `invalid_credentials` (same for unknown email), 429 + Retry-After |
| POST /auth/refresh | refresh cookie | | 200 `Me` + new cookies | 401 (cookies cleared; reuse of an old token revokes the whole session family) |
| POST /auth/logout | none | | 204, cookies cleared, refresh family revoked | |
| GET /me | user | | 200 `Me` | 401 |
| PATCH /me | user | `{display_name?, education_level?, target_roles?[≤10]}` | 200 `Me` | 422 |
| GET/PATCH /me/consents | user | `{voice_transcript?, analytics?}` | 200 `{voice_transcript, analytics}` (both default false) | |
| DELETE /me | user | `{password}` | 204, account + dependent rows deleted | 403 `wrong_password` |

`Me` = `{id, email, role, created_at, profile:{display_name, education_level, target_roles}, consents:{voice_transcript, analytics}}`.
Rate limits (in-memory, per process): login 5 failures per email+IP and 20 per IP per 15 min; signup 10 per IP per hour.
Not implemented: email verification, password reset, admin endpoints.

## Implemented in Phase 3 ✅ (companies)
All require login. Public responses contain only `verified_lahore` companies with a Lahore location.
| Endpoint | Notes |
|---|---|
| GET /companies?q=&locality=&tech=&page=&page_size= | `{items[],total,page,page_size}`; page_size 1-50; locality/tech/q are case-insensitive; item = `{slug,name,description,tech_focus,localities,website,careers_url,last_verified_at,needs_recheck,evidence_count}` |
| GET /companies/localities | sorted list of Lahore localities that have a verified company |
| GET /companies/{slug} | item + `locations[{id,locality,address,is_lahore,verified_at}]` (Lahore only) + `sources[{id,url,source_type,label,stored_label,retrieved_at,excerpt}]` (active only; `label` becomes `unverified_or_outdated` past its freshness limit). 404 for anything not verified |

Admin (role `admin`; 403 otherwise; CSRF required on writes):
| Endpoint | Notes |
|---|---|
| GET /admin/companies?status= | `[{id,slug,name,verification_status,locations,sources,last_verified_at}]` |
| POST /admin/companies | `{name, slug?, website?, careers_url?, description?, tech_focus?}` -> 201, always `candidate`; unknown fields (e.g. status) -> 422 |
| GET /admin/companies/{id} | full record incl. all sources (with `status`, `supports_lahore`) and verification history |
| PATCH /admin/companies/{id} | `{website?, careers_url?, description?, tech_focus?}`; cannot change status |
| POST /admin/companies/{id}/locations | `{locality, address?, is_lahore}`; 409 on duplicate |
| POST /admin/companies/{id}/sources | `{url, source_type, label, supports_lahore, excerpt, retrieved_at}`; 422 `label_mismatch`, `future_date`, `naive_datetime`; 409 duplicate URL |
| PATCH /admin/companies/{id}/sources/{sid} | `{status: unreviewed|active|rejected}` |
| POST /admin/companies/{id}/verification | `{decision: verified|rejected|marked_stale, evidence_ids[], notes}`; 422 `verification_requirements_not_met` with `details` listing what is missing |

CLI (run from `apps/api`): `python -m app.cli import-seed`, `make-admin <email>`, `stale-check`.

## Implemented in Phase 4 ✅ (resumes). All require login; user-owned (another user's ID -> 404). Writes need CSRF.
| Endpoint | Notes |
|---|---|
| GET /roles | `[{slug,title}]` from the general role catalog |
| GET /resumes | newest first. `ResumeOut` = `{id,filename,kind,size_bytes,pages,created_at,analyzed,duplicate,latest,injection_signals[],truncated}`. Never includes stored text, storage key or contact details |
| POST /resumes | multipart field `file` (.pdf/.docx, max `MAX_UPLOAD_MB`=5). 201 `ResumeOut`; 200 with `duplicate:true` if the same file was already uploaded. Errors: 413 `file_too_large`, 415 `unsupported_type`/`content_mismatch`, 422 `empty_file`/`encrypted_pdf`/`encrypted_docx`/`macros_not_allowed`/`file_too_complex`/`too_many_pages`/`corrupt_file`/`no_text`/`parse_timeout`/`parse_failed`, 409 `resume_limit` (10 per user), 429 (10 uploads/hour) |
| GET /resumes/{id} | `ResumeOut` |
| POST /resumes/{id}/analyze | Runs the AI extraction, saves a new version, returns `ResumeOut` with `latest` = `{id,created_at,provider,model,schema_version,parsed,report}`. `parsed` = education, experience, projects, skills (`source` stated/inferred), achievements, inferences. `report` = `{retries,dropped_ungrounded,downgraded_to_inferred,injection_signals,truncated}`. Errors: 503 `llm_not_configured`/`llm_unavailable`, 502 `analysis_failed` (nothing saved), 429 (`ai_rate_limited` or 10 analyses/hour) |
| GET /resumes/{id}/fit?role=slug | Deterministic comparison of the latest analysis with a general role skill list: `{role,catalog_version,catalog_note,required{matched[],missing[],coverage_stated,coverage_with_inferred},preferred{...},notes[],disclaimer,resume_version_id}`. 409 `not_analyzed`, 404 unknown role |
| DELETE /resumes/{id} | 204; deletes rows, versions and the stored file |
`DELETE /me` now also deletes the user's stored resume files.

Provider interface (Python): `LLMProvider.complete_json(messages) -> str` with `name`, `model`; errors `LLMNotConfigured`, `LLMRateLimited`, `LLMUnavailable`, `LLMInvalidOutput`. `generate_structured(provider, Schema, messages, max_retries=2)` validates and retries. Storage: `StorageProvider.put/get/delete`.

## Implemented in Phase 5 ✅ (research and company matching)
Admin only (role `admin`; CSRF on writes):
| Endpoint | Notes |
|---|---|
| POST /admin/companies/{id}/research?force=false | 202 `RunOut` `{id,status,error_code,summary,started_at,finished_at,cached}`. The work runs in the background; poll the company. `cached:true` returns a run under 7 days old. Errors: 409 `company_not_verified`, 409 `research_in_progress`, 503 `research_not_configured`, 429 (10 runs/hour) |
| GET /admin/companies/{id}/research | last 10 runs, newest first |
| GET /admin/companies/{id} | now also returns `findings[]` (all statuses: `{id,kind,role_title,text,skills,years_experience,scope,label,source_url,source_type,retrieved_at,status,source_id,source_status}`) and `latest_run` |
| PATCH /admin/companies/{id}/findings/{fid} | `{status: unreviewed|active|rejected}`; approving also approves its source; 409 `source_rejected` |
Run `status`: `running`, `succeeded` (new findings saved), `partial` (sources only, or nothing usable), `unavailable` (search provider down/not configured/rate limited; nothing changed), `failed` (unexpected; nothing saved). `summary` has counts, `warnings[]` codes, `conflicts[]`, `message`.
Run `summary.warnings` codes: `no_official_site`, `ai_not_configured`, `ai_unavailable`, `ai_output_rejected`, `some_pages_not_fetched`, `fetch_failed_using_snippets`.

Users:
| Endpoint | Notes |
|---|---|
| GET /companies/{slug} | now includes `requirements[]` = approved findings only: `{id,kind,role_title,text,skills,years_experience,scope,label,source_url,retrieved_at}`; `label` is the effective evidence label (degrades to `unverified_or_outdated` past its freshness limit) |
| GET /resumes/{id}/fit?role=slug&company=slug | optional `company` (verified only, else 404) adds `company`: `{available:false, reason}` or `{available:true, skills[{skill,weight,have: stated|inferred|null, reasons[], sources[]}], coverage_stated, coverage_with_inferred, evidence_count, notes[]}`. Weights: official 1.0, candidate report 0.5, outdated/unverified 0.25 |

Provider interface: `ResearchProvider.search(query, max_results, include_domains, exclude_domains) -> list[SearchHit]`, `.extract(urls) -> list[Page]`; errors `ResearchNotConfigured`, `ResearchRateLimited`, `ResearchUnavailable`. `BudgetedProvider` caps calls per run.

## Implemented in Phase 6 ✅ (assessments). Login required; user-owned (another user's ID -> 404); writes need CSRF.
| Endpoint | Notes |
|---|---|
| POST /assessments | `{resume_id, role, company?, question_count (10-30, default 20), duration_minutes? (10-120)}` -> 202 `Assessment` with `status:"generating"`; writing happens in the background (poll GET). Errors: 404 (resume/role/company not visible), 409 `not_analyzed` / `generation_in_progress` / `assessment_limit` (30 kept), 503 `llm_not_configured`, 429 (3 per hour) |
| GET /assessments | newest first; includes `score {mcq_correct, mcq_total}` once submitted |
| GET /assessments/{id} | `Assessment` = `{id,status,mode,role,company,notice,question_count,duration_minutes,created_at,started_at,deadline_at,submitted_at,auto_submitted,server_now,error_code,message,generation{accepted,target,dropped,warnings},score,questions,answers}`. `status`: `generating`, `ready`, `in_progress`, `submitted`, `failed`. `questions`/`answers` only while `in_progress`. An expired test (deadline + 30 s) is auto-submitted on access |
| POST /assessments/{id}/start | ready -> in_progress; sets the server deadline; idempotent |
| PUT /assessments/{id}/answers | `{answers:[{question_id, selected_index?, response_text? (max 4000)}]}` upsert (autosave). 409 `not_in_progress`, 409 `time_expired`, 422 `unknown_question`/`wrong_answer_type`/`bad_option`/`duplicate_answer` |
| POST /assessments/{id}/submit | grades multiple choice, returns `Review`; idempotent |
| GET /assessments/{id}/review | `{assessment, questions[{...question, correct_index, reference_points, explanation, selected_index, response_text, is_correct, needs_evaluation}], result{mcq_correct,mcq_total,mcq_unanswered,short_answered,short_total,evaluated:false,by_topic[],note}}`; 409 `not_submitted` before submission |
| DELETE /assessments/{id} | 204 |
Question while running: `{id,position,type: mcq|short_answer,category: technical|role_problem_solving|resume_project|company_informed,prompt,options[{index,text}],difficulty,topic,label:"ai_generated_practice",informed_by[{url,label}],max_points}`. **No answer key, reference points or explanation until submitted.**
Failure codes (`error_code`): `ai_not_configured`, `ai_unavailable`, `insufficient_valid_questions`, `resume_missing`, `timed_out`, `internal_error`.

## Implemented in Phase 7 ✅ (coding). Login required; sessions and submissions are user-owned (404 otherwise); writes need CSRF.
| Endpoint | Notes |
|---|---|
| GET /coding/runner | `{mode: mock|http, executes_code, reachable, backend, message}`. Today `executes_code` is always false |
| GET /coding/problems?role=&difficulty=&topic= | `[{slug,title,difficulty,minutes,topics,roles}]` |
| GET /coding/problems/{slug} | statement, constraints, signature, starter code, examples, **visible tests only**, `hidden_count`, `per_test_ms`, `label: ai_generated_practice`. Never hidden tests, solution, approach or complexity |
| POST /coding/sessions | exactly one of `{problem_slugs: [1-3]}`, `{assessment_id}` (must be submitted), `{role, count 1-3}`. 201 `Session`. 409 `session_in_progress` (details.session_id) / `session_limit` / `assessment_not_submitted` / `no_problems_for_role` |
| GET /coding/sessions, GET /coding/sessions/{id} | `Session` = `{id,status: in_progress|submitted,assessment_id,problem_slugs,problems (only while in progress),drafts,progress[],started_at,deadline_at,submitted_at,auto_submitted,server_now,runs_left,submits_left}`. An expired session (deadline + 30 s) is finished automatically on access |
| PUT /coding/sessions/{id}/drafts/{slug} | `{code}` autosave (max 20,000 bytes, no NUL) |
| POST /coding/sessions/{id}/run | `{problem, code, language: "python"}`: runs the **visible** tests. Max 30 per session |
| POST /coding/sessions/{id}/submit | runs visible + hidden tests. Max 5 per problem. The last submission counts |
| both return `Submission` | `{id,kind,problem,status: completed|not_executed,executed,compile_error,passed_count (null when not executed),total_count,runtime_ms,runner_backend,message,results[],feedback}`. `results[]` rows: visible = `{id,hidden:false,label,status,runtime_ms,args,expected,actual,error,stdout}`; hidden = `{id:"hidden-N",hidden:true,label:"Hidden test N",status,runtime_ms}` only |
| POST /coding/sessions/{id}/finish, GET .../review | `Review` = `{session, problems[{problem,approach,complexity,reference_solution,final_code,runs,submits,submission,passed_count,total_count,solved}], summary{solved,problems,tests_passed (null unless every problem ran),tests_total,executed,note}}`. 409 `not_submitted` before finishing |
| POST /coding/submissions/{id}/feedback | subjective AI commentary `{complexity,strengths[],improvements[],readability,label:"ai_commentary_subjective",note,...}`; only for submissions, only after the session is finished (409 `finish_first`); cached; 502 `feedback_failed`, 503 `llm_not_configured`/`llm_unavailable`, 429 |
| DELETE /coding/sessions/{id} | 204 |
Errors: 503 `runner_unavailable` (nothing is counted), 502 `runner_error` (reply failed validation, discarded), 429 `run_limit` / `submit_limit` / `rate_limited`, 409 `time_expired` / `not_in_progress`, 422 `unknown_problem` / `empty_code` / `invalid_code` / `code_too_large`. A NUL character in submitted code is now refused earlier, for every route, as 422 `invalid_input` (see Cross-cutting errors).
CLI: `python -m app.cli import-problems`.

**Runner contract** (API -> `POST {RUNNER_URL}/execute`; headers `X-Runner-Timestamp` and `X-Runner-Signature` = hex HMAC-SHA256 of `"{timestamp}." + raw body` with the shared secret): request `{request_id, language: "python", entry_point, code (<=20000), tests[{id,args,expected,tolerance?}] (1-60), limits{per_test_ms,total_wall_s,memory_mb,output_kb}}`; response `{request_id, backend, backend_version, executed, compile_error, tests[{id,status: passed|failed|error|timeout|not_run,runtime_ms,actual,error,stdout}], total_runtime_ms}`. `GET /health` -> `{status,backend,version,executes_code,contract}`.

---
# Proposed contracts for later phases ⏳ (PROPOSED, not implemented)

Base: `/api/v1`. JSON. Auth: httpOnly cookie session unless marked public. All user-scoped resources enforce ownership (404 for another user's ID).
Error body: `{"error":{"code":"string","message":"string","details":{}}}`. Codes: 400 validation, 401, 403, 404, 409, 413 (upload too large), 415 (bad file type), 422 (schema), 429 (rate limit), 502/503 (provider unavailable).

## Endpoints
| Group | Method + path | Auth | Notes |
|---|---|---|---|
| Health | GET /health | public | liveness |
| Auth | POST /auth/signup, /auth/login, /auth/logout, /auth/refresh | public/cookie | rate limited |
| Me | GET/PATCH /me; DELETE /me (data deletion); GET/PATCH /me/consents | user | |
| Companies | GET /companies?q=&locality=&tech=&page= | user | returns only `verified_lahore` |
| | GET /companies/{slug} | user | includes evidence items with labels |
| | POST /admin/companies, PATCH /admin/companies/{id}, POST /admin/companies/{id}/verification | admin | verification needs evidence ids + decision |
| Roles | GET /roles | user | |
| Resumes | POST /resumes (multipart PDF/DOCX), GET /resumes, GET /resumes/{id}, DELETE /resumes/{id} | user | analysis is a job |
| Jobs | GET /jobs/{id} | user | status: queued/running/succeeded/failed |
| Research | POST /companies/{slug}/research | user | starts job; may return cached bundle with freshness info |
| Fit | POST /fit-analyses {resume_id, role_id, company_slug?} | user | |
| Assessments | POST /assessments, GET /assessments/{id}, PUT /assessments/{id}/answers, POST /assessments/{id}/submit | user | correct keys never returned before submit |
| Coding | GET /coding/problems/{id}, POST /coding/run (visible tests), POST /coding/submit (hidden tests) | user | executes only via runner |
| Interviews | see "Interviews (Phase 8)" below | user | text fallback uses same endpoints |
| Reports | see "Reports (Phase 9)" below | user | |

## Provider interfaces (Python Protocols)
- `LLMProvider.generate_structured(schema, messages, *, max_retries=2) -> BaseModel`
- `ResearchProvider.search(query, *, max_results) -> list[SearchHit]`; `.extract(urls) -> list[ExtractedPage]`
- `StorageProvider.put/get/delete(key)`
- `SpeechProvider` (frontend): `startListening/stopListening/speak` with capability detection
- `SandboxClient.run(language, code, tests, limits) -> RunResult` (contract with runner below)

## Runner contract (service-to-service)
`POST /execute` with header `X-Runner-Signature` (HMAC of body). Body: `{language, source, tests:[{id,input,expected,hidden}], limits:{cpu_s,wall_s,memory_mb,output_kb}}`. Response: `{status, tests:[{id,passed,runtime_ms,stdout_excerpt?}], runner_version}`; hidden test details are stripped server-side before returning to the browser.

## Interviews (Phase 8) — all require login; other users' interviews return 404
| Method and path | Body | Result / errors |
|---|---|---|
| POST /interviews | `{resume_id, role, company?, question_count 4-10, input_mode voice\|text, consent: true, save_transcript?}` | 201 interview. 422 `consent_required`; 404 resume/role/company (unverified companies are invisible); 409 `not_analyzed`, `interview_in_progress` (details.interview_id), `interview_limit`; 429; 503 `llm_not_configured` |
| GET /interviews | | list (no turns) |
| GET /interviews/{id} | | interview with `turns` (null once the transcript is removed) |
| POST /interviews/{id}/answer | `{text, source typed\|speech}` or `{skip: true}` | interview with the next interviewer turn. 409 `interview_ended`, `not_your_turn`; 422 `empty_answer`; 429 (checked before saving). AI trouble never fails the call: a built-in question (`source: "fallback"`) is used |
| POST /interviews/{id}/event | `{kind: mic_denied\|speech_unsupported\|speech_error\|tts_unavailable}` | first three switch `input_mode` to text. 409 if not active |
| POST /interviews/{id}/end | | status `completed` |
| POST /interviews/{id}/resume | | interrupted -> active. 409 `interview_in_progress`, `transcript_gone`, `invalid_state` |
| POST /interviews/{id}/evaluate | | `{interview, evaluation}`; cached after the first success. 409 `end_first`, `nothing_to_evaluate`, `transcript_gone`; 429 `ai_rate_limited`; 502 `evaluation_failed` (nothing saved); 503 |
| GET /interviews/{id}/review | | `{interview, evaluation|null}` |
| DELETE /interviews/{id}/transcript | | removes turns; scores and notes stay. 409 `interview_active` |
| DELETE /interviews/{id} | | 204; removes everything |

Interview object: `status active|completed|interrupted`, `mode general|company`, `label: "ai_generated_practice"`, `awaiting_answer`, `questions_asked`, `answers_given`, `save_transcript`, `transcript_available`, `evaluated`, `notice`. Turn: `kind opening|question|follow_up|answer|skipped|closing`, `source ai|fallback|system|typed|speech`, `informed_by [{n, url, label}]` (only approved company evidence).
Evaluation object: `label: "ai_evaluation_subjective"`, `rubric_version: "voice-1"`, `criteria [{key, score 0-4, rationale, evidence_turns, low_evidence}]`, `indicator` (0-100 or null), `answers_scored`, `evidence_level limited|adequate`, `strengths`, `improvements`, `per_answer`, `caveats`, `provider`, `model`, `injection_signals`, `transcript_kept`.

## Reports (Phase 9) — all require login; other users' reports and sources return 404
| Method and path | Body / query | Result / errors |
|---|---|---|
| POST /reports | `{role, resume_id?, assessment_id?, coding_session_id?, interview_id?, horizon 7\|30}` | 201 report. 409 `nothing_to_report` (no assessment, coding session or interview), `not_submitted`, `not_evaluated`, `not_analyzed`, `report_limit`; 422 `role_mismatch`; 404 unknown role or not yours; 429 |
| GET /reports?role= | | summaries newest first: `overall` (or null), `scores`, `included`, `missing` |
| GET /reports/sources?role= | | finished assessments, coding sessions (with `executed`), evaluated interviews and analysed resumes for that role |
| GET /reports/progress?role= | | `{series:[{report_id, created_at, role, overall, scores}], latest_change, note}` |
| GET /reports/{id} | | full report incl. `previous` comparison |
| POST /reports/{id}/roadmap | `{horizon 7\|30}` | report with a new plan; scores unchanged |
| DELETE /reports/{id} | | 204 |

Report: `rubric_version`, `rubric` (as used), `components [{key, kind objective\|subjective, status available\|missing\|not_run\|not_scored, value 0-100\|null, reason, low_evidence, detail, how}]`, `overall {value\|null, included, subjective_share, note, limited, missing[]}`, `gaps [{label, severity, kind, evidence[]}]`, `strengths`, `practice_questions` (labelled `ai_generated_practice`), `sources` (approved company evidence with url and label), `roadmap {source ai\|built_in, horizon, note, items[{when, focus, tasks, minutes}]}`, `notes`, `previous`, `disclaimer`.

## Cross-cutting errors (Phase 10)
- 400 `invalid_input`: a NUL character (`%00`) in a path or query string. 422 `invalid_input`: a NUL character anywhere in a JSON body (keys included), or a database data error. 413 `too_large`: a JSON body over 1 MiB. Every JSON response carries `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, a restrictive `Content-Security-Policy`, and `Cache-Control: no-store` under `/api/`; production adds `Strict-Transport-Security`.
- Anonymous visitors may call only: `GET /health`, `GET /auth/csrf`, `POST /auth/signup`, `POST /auth/login`, `POST /auth/logout`. `/auth/refresh` needs the refresh cookie. A test fails if any other route answers without login.

## Account and runner additions (Phase 12)
- `POST /me/password` `{current_password, new_password 8-128 chars}` (login and CSRF required; unknown fields refused) returns 204 and fresh cookies for this device; every other session is revoked. Errors: 403 `wrong_password` (counted by the login throttle; at the limit 429 `rate_limited` with `Retry-After`), 422 `same_password`, 422 validation.
- `python -m app.cli reset-password <email>` (admin, local): hidden password prompt, signs the user out everywhere.
- Runner service `GET /health` now includes `backend: "bwrap"` and `executes_code: true` when the real sandbox is active. `POST /execute` is unchanged (HMAC signed). A killed or hung test is `timeout`; the reply never contains `not_run` when `executed` is true.
