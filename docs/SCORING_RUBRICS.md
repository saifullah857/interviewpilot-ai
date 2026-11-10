# SCORING_RUBRICS.md — rubric `report-1`
_Defined before the report code was written (Phase 9). The same text is stored inside every report (`reports.rubric`), so an old report always shows the rules it was scored under. Changing a weight or definition means a new version, `report-2`; old reports keep `report-1`._

## Principles
1. **Objective and subjective stay apart.** Objective = computed by the server from stored results (answer keys, runner test counts, resume text). Subjective = an AI's judgement of interview answers. Every component carries `kind`, and the report screen shows them in separate lists.
2. **Nothing is guessed.** No data means "missing", a runner that did not execute code means "not run", an undefined metric means "not scored". None of these becomes a number, and none counts as zero.
3. **No AI computes a number in a report.** The AI only words the improvement plan, sees gap names (never scores), and its output is rejected if it has unknown fields, an unknown focus, a link, an out-of-range day, or instruction-like text.
4. **No claim of validity.** Scores are preparation indicators for tracking your own progress. They are not hiring predictions, not comparable between people, and not scientifically validated.

## Components
| Key | Kind | Value (0 to 100) | In overall? | Missing / not-run behaviour |
|---|---|---|---|---|
| `resume_fit` | objective | share of the role's required skills that the resume **states** (not AI-inferred) | no (describes the document) | missing if no resume chosen |
| `technical_knowledge` | objective | correct multiple-choice answers / total, unanswered counts as wrong; short answers saved but **not scored** | yes, 0.35 | missing if no assessment or no MCQs; flagged limited if fewer than 5 MCQs |
| `coding_correctness` | objective | tests passed by the **last submission per problem**, only when the runner really executed it; an unsubmitted problem counts 0 passed (with a note) | yes, 0.35 | `missing` if nothing was submitted; `not_run` if any last submission was not executed (e.g. the development mock) |
| `interview_performance` | subjective | mean of four interview criteria (0 to 4 each) as a percentage | yes, 0.30 | missing if no interview or no feedback yet; flagged limited with fewer than 3 answers |
| `problem_solving` | subjective | the interview `reasoning` criterion as a percentage | no (same evidence, not counted twice) | follows the interview |
| `communication` | subjective | mean of `clarity` and `specificity` as a percentage (text only; delivery not assessed) | no (same evidence) | follows the interview |
| `complexity_analysis` | subjective | **not scored** in this version | no | always `not_scored` |

## Overall preparation indicator
Weighted average of the in-overall components that exist (`available`), with weights renormalised over those present. Example: technical 100 and interview 62 give (0.35·100 + 0.30·62) / 0.65 = 81. It is `null` when no weighted component exists. The report states how many of the 3 weighted components it used, the share of the number that comes from AI judgement, and whether evidence is limited.

## Gaps, strengths and practice
- Gaps (max 8), sorted by severity then measured-before-judged: required resume skills not stated (high); assessment topics with fewer than half correct, at least 2 questions (high below one third, otherwise medium; a single wrong question is low); coding problems not fully passed (high below half the tests, otherwise medium); interview criteria scored 0 or 1 **that cite at least one real answer** (0 high, 1 medium). Each gap lists its evidence.
- Strengths: assessment topics with at least 80% correct (2+ questions), stated required skills, fully passed coding problems, interview criteria scored 3 or 4 that cite answers.
- Practice: up to 5 missed multiple-choice prompts (labelled AI-generated practice) and up to 3 unsolved coding problems. Nothing new is generated, so nothing can be invented.

## Roadmap
7-day (`Day n`, `Days a-b`) or 30-day (`Week 1` to `Week 4`, `Day n`) plan. Focus names must be a real gap or "Mixed review" / "Mock interview". If the AI is unavailable, unconfigured or rejected, a built-in plan from the gaps is used and labelled so. Regenerating a plan never changes a score.

## Comparison and progress
A report is compared with the previous report for the same role: only components available in both are compared. The screen says that attempts use different questions, so small changes are not meaningful. Progress charts need two scored reports.

## Known limits of this rubric
Short answers and complexity explanations are unscored; the weights (0.35 / 0.35 / 0.30) are a judgement call, not derived from data; interview scores rest on AI judgement of text; resume fit is a skill-name comparison against the role catalog.
