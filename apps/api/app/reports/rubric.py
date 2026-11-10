"""Scoring rubric, version `report-1`. The same definitions are stored inside every report, so an old report always shows the rules it was scored under.
Objective = computed from stored results (test counts, answer keys, resume text). Subjective = an AI's judgement of interview answers.
Nothing here is scientifically validated, and no number is a prediction of hiring."""

RUBRIC_VERSION = "report-1"

# in_overall: whether the component feeds the overall preparation indicator, and with what weight (renormalised over the components that exist).
COMPONENTS = [
    {"key": "resume_fit", "name": "Resume-to-role fit", "kind": "objective", "weight": 0.0,
     "how": "Share of the role's required skills that your resume states. Missing skills may simply be missing from the resume, not from you. Not part of the overall indicator because it describes the document, not your performance."},
    {"key": "technical_knowledge", "name": "Technical knowledge", "kind": "objective", "weight": 0.35,
     "how": "Multiple-choice questions answered correctly in a submitted assessment, as a percentage. Unanswered counts as wrong. Short answers are saved but not scored in this version."},
    {"key": "coding_correctness", "name": "Coding correctness", "kind": "objective", "weight": 0.35,
     "how": "Tests passed by your last submission for each problem, measured by a code runner that really executed the code. A problem you did not submit counts as 0 passed. If the runner did not execute code, there is no score."},
    {"key": "interview_performance", "name": "Interview performance", "kind": "subjective", "weight": 0.30,
     "how": "Average of the four interview criteria (technical correctness, reasoning, clarity, specificity), each scored 0 to 4 by an AI from the text of your answers, as a percentage."},
    {"key": "problem_solving", "name": "Problem-solving and reasoning", "kind": "subjective", "weight": 0.0,
     "how": "The interview 'reasoning' criterion as a percentage. Same evidence as interview performance, so it is shown but not counted twice."},
    {"key": "communication", "name": "Communication and explanation", "kind": "subjective", "weight": 0.0,
     "how": "Average of the interview 'clarity' and 'specificity' criteria as a percentage. Judged from text only; speech delivery is not assessed. Not counted twice."},
    {"key": "complexity_analysis", "name": "Complexity analysis", "kind": "subjective", "weight": 0.0,
     "how": "Not scored in this version. It would need a real code runner and a validated way to judge complexity explanations."},
]
BY_KEY = {c["key"]: c for c in COMPONENTS}
OVERALL_HOW = (
    "Weighted average of the technical knowledge, coding correctness and interview components that exist, with the weights renormalised over those present. "
    "It is a preparation indicator for you to track over time. It is not a prediction of being hired and is not comparable between people."
)
LOW_EVIDENCE_MCQ = 5  # fewer multiple-choice questions than this: flagged as limited evidence

RUBRIC = {"version": RUBRIC_VERSION, "components": COMPONENTS, "overall": OVERALL_HOW}
DISCLAIMER = (
    "Scores are preparation indicators, not guarantees of selection or hiring. Objective scores come from stored results; subjective scores are AI judgements. "
    "Questions are AI-written practice, not real company questions."
)
