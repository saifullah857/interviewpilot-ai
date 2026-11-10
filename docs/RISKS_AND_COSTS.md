# RISKS_AND_COSTS.md (Phase 0, researched 2026-10-14)

## 1. External services and costs
| Service | What we use it for | Cost/limits found | Confidence |
|---|---|---|---|
| Groq (LLM) | All agent reasoning | Free tier with no card; third-party sources cite about 30 requests/min and 1,000 requests/day on the free tier, no privacy guarantees on free tier, and a Developer tier with higher limits. Per-model token limits are likely the tighter constraint. | **Medium-low** (third-party pages; confirm at console.groq.com/settings/limits before Phase 4) |
| Tavily (research) | Search and page extraction | Official docs: free plan 1,000 credits/month; basic search 1 credit, advanced 2; extract 1 credit per 5 URLs; pay-as-you-go $0.008/credit. | **High** (official docs) |
| Code runner | Python execution | Local Docker Desktop/WSL2: $0 licence for personal/small use as far as I know (verify current terms); hosted judge APIs: pricing not verified. | Low until decided |
| PostgreSQL, Python, Node, Git | Dev stack | Free/open source | High |
| Voice | Browser speech APIs | $0 | High on cost; support varies by browser |

Rough dev-budget math (estimates, not measurements): one company research refresh ≈ 6 basic searches + ~10 extractions ≈ 8 credits, so ~100+ refreshes per free month. A full user journey ≈ 40–50 LLM calls (resume 2, fit 1, generation 3–5, interview ~30, report 2–3), so a ~1,000 requests/day limit supports roughly 20 journeys/day, assuming token limits don't bite first. **Expected MVP dev cost: $0** if free tiers hold; tokens-per-minute throttling is the likely pain point.

## 2. Technical risks
| Risk | Severity | Mitigation |
|---|---|---|
| Unsafe code execution | Critical | Separate runner; ADR-006 decision; adversarial isolation tests; mock clearly labelled if unresolved |
| Company data staleness/wrong Lahore claims | High | Evidence rows, human review gate, freshness policy, labels |
| Unreliable/unavailable interview reports (sites block bots, ToS limits, old or fake reviews) | High | Treat as `public_candidate_report`, link out, store paraphrases only, show "not enough public data" instead of inventing |
| Prompt injection via resumes/web pages | High | Data-framing, no tools beyond search/fetch, schema validation, injection test fixtures |
| LLM hallucinated questions/answer keys | High | Validator pass, second-pass key check, labels, sampling QA |
| Groq free-tier rate limits/privacy | Medium | Provider abstraction, retry/backoff, cache, avoid sending unnecessary PII, tell users |
| Voice support differences (browser-dependent, vendor servers process audio) | Medium | Text fallback, capability detection, privacy notice |
| Resume parsing quality (scanned PDFs, odd layouts) | Medium | Clear errors, OCR out of MVP, user can edit parsed data |
| Windows setup friction (Postgres, Docker/WSL2) | Medium | Step-by-step PowerShell guides, `scripts/` helpers, SQLite test fallback |
| Chat-based workflow: file drift between sessions | Medium | Durable docs, manifest, archives per checkpoint, Git |
| Scope creep / over-engineering | Medium | Phase gates, modular monolith, no Celery/K8s |
| Scores misread as hiring odds | Medium | Explicit wording in UI and reports |

## 3. Alternatives considered
LLM: Groq (chosen, cheap/fast, free dev tier) vs OpenRouter vs local models (heavy on Windows). Search: Tavily vs Brave/Serper/SearXNG (unevaluated). Orchestration: LangGraph (chosen for explicit state) vs plain functions (used where no branching).
