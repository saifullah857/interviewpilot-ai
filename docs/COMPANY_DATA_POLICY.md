# COMPANY_DATA_POLICY.md (v0.3, Phase 5: rules below are enforced in code and tests unless marked "policy only")

## 1. Lahore eligibility
A company is eligible only if there is evidence of a physical office or business presence in Lahore, Pakistan: e.g., an official contact/careers page listing a Lahore address, or a posting on an official channel naming a Lahore office. Remote-only roles from overseas employers without a Lahore office are **ineligible**.

## 2. Statuses and who can change them (enforced)
`candidate` (default for everything imported or created) -> `verified_lahore` | `rejected`; `verified_lahore` -> `stale`; `stale`/`rejected` can be verified again.
- Nothing can be created or imported as verified. The seed file and the create endpoint reject a status field.
- Only an admin can change status, through a verification decision stored with reviewer, date, notes and the evidence IDs used.
- **Verifying requires all of:** at least one location marked as Lahore; at least one selected source labelled `official_verified` that is marked "shows a Lahore office"; review notes of 10+ characters. The reviewer is a human.
- Rejecting requires notes. Marking stale is only possible from `verified_lahore`.
- Selected sources become `active` when the company is verified; `unreviewed` sources are never shown to users.

## 3. What users can see (enforced)
- The directory and company pages return only `verified_lahore` companies that have a Lahore location. Candidates, rejected and stale companies look the same as missing ones (404).
- Only locations marked Lahore and only `active` sources are shown. Admin-only fields (review status, "supports Lahore") are never in public responses.

## 4. Source classification (enforced)
| Label | Allowed source types | Display rule |
|---|---|---|
| official_verified | official_website, careers_page, job_posting, registry | Link + retrieval date |
| public_candidate_report | candidate_report | "Reported by a candidate", never as current policy |
| unverified_or_outdated | any | Shown with warning |
| ai_generated_practice | not a research source (rejected) | Belongs to assessments (Phase 6) only |

Required per source: http(s) URL (unique per company), type, label, retrieval date with timezone and not in the future, short excerpt in your own words (max 500 characters, not copied text).

## 5. Freshness (enforced for display; automation is manual)
- Office/location evidence: 180 days. Job postings: 30 days. Candidate reports: 12 months.
- Past its limit, a source is **shown as `unverified_or_outdated`** (the stored label is kept).
- A verified company whose last verification is over 180 days old gets a "needs recheck" flag. Run `python -m app.cli stale-check` to move such companies to `stale`, which hides them. It is **not scheduled automatically yet**.

## 6. Automated research (Phase 5, enforced)
- **Who and when:** only an admin can start research, only for a `verified_lahore` company. A run less than 7 days old is reused unless forced. One run at a time per company; 10 runs per admin per hour.
- **Budget:** at most 4 searches and 6 page fetches per run, enforced by a wrapper whatever the workflow tries.
- **Classification is deterministic.** A page is "official" only if its host is the company's saved website domain or a subdomain of it (look-alikes such as `evil-acme.com` or `acme.com.evil.net` are not). Without a saved website, nothing is called official. Raw IPs, localhost, internal names and non-http(s) URLs are ignored.
- **Interview-report sites and job boards** (Glassdoor, Reddit, AmbitionBox, Quora, Blind, LinkedIn, Indeed, Rozee, Mustakbil, Bayt, social networks) are **never fetched**; only the short search snippet is used. Report-site content can only produce `interview_format` findings. Pages that never name the company are discarded.
- **Findings** are short paraphrases written by the AI, kept only if the AI's supporting snippet is found in the page text; the snippet is then discarded, so no third-party text is stored (only a content hash). Findings and any new sources start `unreviewed` and are invisible to users until an admin approves them. Approving a finding approves its source; rejecting a source rejects its findings.
- **Lahore scope:** a finding is tagged `lahore` only if the page text mentions Lahore; otherwise `unspecified` and shown as "Location not stated".
- **Freshness:** a finding's age counts from the day it was retrieved, using the same limits as section 5. Retrieved is not the same as posted: a page can be older than the day we read it.
- **What research does not do:** no salaries, benefits, recruiter names or emails are extracted. Sources are never added by the AI, only by our own search step.

## 7. Conflicts and gaps
Conflicts are detected for one case only: different "years of experience" for the same role from different sources are listed on the run and never silently resolved. Other kinds of conflict are not detected yet. If research finds nothing usable the run says there is not enough public information. Missing data shows as "not found". The app never invents interview rounds, recruiter names, emails, addresses, vacancies, salaries, hiring status, or policies.

## 8. Use of company evidence in practice assessments (Phase 6, enforced)
- Only **approved** findings whose evidence label is currently `official_verified` or `public_candidate_report` (not outdated) and whose role fits the chosen role can inspire a question. Unreviewed, rejected, outdated or other-role evidence is never used.
- Every generated question is labelled `ai_generated_practice` (a database constraint forbids any other label). A question inspired by company evidence links to its sources and says it is **not** a question the company asked. Text claiming otherwise ("was asked at...", "actual interview question") is rejected automatically.
- If a company is chosen but has no usable approved evidence, the assessment is general role preparation and says so; it is never presented as company-specific.

## 9. Content handling
Fetched web content is untrusted data. Store links and short paraphrases, not copied reviews. Publicly listed recruitment contacts only from an official page (not implemented yet).

## 10. Seed data
`data/company_seed/lahore_candidates.json` holds 14 **names only** from the project brief. No website, address, source or description is recorded for them. A single web search in Phase 3 for one company returned only third-party directory pages, not official pages, so nothing was recorded. As of Phase 3, **no real company is verified**. Verification is done by the admin adding official sources and deciding (see SETUP_WINDOWS.md, section 7).
