# Question bank, screening and readiness: how it works and how to extend it

## What exists
| Part | Where | Count |
|---|---|---|
| Technical and scenario questions | `data/questions/<company>.json` | 25 for each of the 21 software houses = 525 |
| Screening MCQ and output questions | `data/questions/screening/screening.json` | 105 |
| Coding problems (with hidden tests) | `data/coding/problems.json` | 62 (25 easy, 27 medium, 10 hard) |
| Company coding sets | computed, not stored | 25 per company (10 easy, 10 medium, 5 hard) |
| Company focus notes | `data/company_seed/lahore_candidates.json` and `data/company_focus/focus.json` | 21 companies |

Every question has a `source_label`: `verified`, `reported` (both need a `source_note`) or `company_focused_practice`. All current questions are `company_focused_practice`: they are written for a company's technology focus and are **not** that company's real interview questions. Nothing in the app says otherwise.

## Setup and migrations
1. `START.bat` (Windows) applies migrations (`alembic upgrade head`, latest is `0011`), imports companies, coding problems and questions, and starts the API and the website.
2. By hand: `cd apps/api`, then `python -m alembic upgrade head`, `python -m app.cli import-seed`, `python -m app.cli import-problems`, `python -m app.cli import-questions`.
3. Environment variables are in `apps/api/.env` (see `.env.example`). `RUNNER_MODE=local` runs submitted code on this computer. `GROQ_API_KEY` is optional: without it the app uses its built-in fallbacks.

## Add a question
- **In the app (admin):** sign in as an admin, open **Manage questions**, press **Add question**. The same validation as the import applies (needs an ideal answer and 2 key points, or 3+ options with a correct one and an explanation; a duplicate prompt for the same company is refused).
- **By file:** add an object to a `data/questions/<company>.json` file and run `python -m app.cli import-questions`. Existing slugs are updated, new ones are created.
- **Make an admin:** `python -m app.cli make-admin you@example.com`.

## Add a company
Add an entry with `slug`, `name` and `tech_focus` to `data/company_seed/lahore_candidates.json`, run `import-seed`, then add `data/questions/<slug>.json`. Tech focus words are mapped to practice tags in `data/company_focus/focus.json` (`tech_to_tags`).

## Add a role
Add an entry with `slug`, `title`, `required`, `preferred` and `family` to `data/roles/roles.json`. Questions use the role slug in their `roles` list. Missing today: QA Engineer and Data Engineer roles.

## Rebuild the generated files
- Technical questions: edit `scripts/qb_<company>.py`, then `python scripts/build_question_bank.py`.
- Screening questions: edit `scripts/screening_a.py` or `screening_b.py`, then `python scripts/build_screening.py`. Output answers are computed by running the code, so they cannot be wrong.
- Coding problems: edit `scripts/problems_screening_*.py`, `scripts/problems_advanced.py` or `build_coding_problems.py`, then `python scripts/build_coding_problems.py`. Each problem needs a reference solution, 6+ hidden tests and wrong solutions in `apps/api/tests/runner/mutants*.py` that the hidden tests must catch.

## How readiness is calculated
Role + optional company + resume. Parts and weights:

| Part | Weight | Source |
|---|---:|---|
| Skill match | 15 | Role's required (x2) and preferred skills stated on the resume; inferred skills count half; skills tied to the company's focus count 1.5x |
| Role relevance | 10 | Overlap between the company's focus areas and the role's skills (company chosen only) |
| Online screening | 20 | Average of your last 3 finished screening tests for the role |
| Technical assessment | 15 | Latest submitted assessment for the role (objective questions) |
| Coding | 25 | Tests passed in your latest finished coding session for the role (code that really ran) |
| Technical interview | 15 | Latest evaluated mock interview for the role |

A part with no data is **not assessed** and left out; the weights of the other parts are scaled to 100. With no result at all the label is "Resume-based estimate only" (or "Not enough data" without a resume). Match labels: 75+ Strong, 60+ Good, 40+ Needs improvement, below 40 Low. A skill is called strong, improve or weak only after at least 2 answered screening questions on it (or a coding result for data structures and algorithms); otherwise it is "stated on resume, not assessed" or "not assessed and not on resume". This is a preparation estimate, **not a hiring probability**.

API: `GET /readiness?role=&company=&resume_id=`, `GET /readiness/roles`, `GET /readiness/companies?role=`.
