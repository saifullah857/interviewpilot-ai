"""Programmatic quality checks for AI-written questions. These run on every question, whatever the AI claims."""

import difflib
import re

from app.assessments.schemas import GenQuestion
from app.resumes.text import injection_signals, normalize

_URL = re.compile(r"https?://|www\.", re.IGNORECASE)
_MARKUP = re.compile(r"<[^>\n]{1,40}>")
# A generated question must never pretend to be a real company question.
_FAKE_PROVENANCE = re.compile(
    r"\b(was asked|were asked|actually asked|actual (?:interview )?question|real (?:interview )?question|reported (?:interview )?question|"
    r"asked (?:at|by|in)|(?:company|interviewers?) (?:asks|asked|always asks)|guaranteed|will (?:definitely )?be asked)\b",
    re.IGNORECASE,
)
_VAGUE_OPTIONS = ("all of the above", "none of the above", "both a and b", "a and b", "all of these", "none of these")
_STOP = {
    "the",
    "a",
    "an",
    "of",
    "to",
    "in",
    "is",
    "are",
    "what",
    "which",
    "how",
    "do",
    "does",
    "for",
    "and",
    "or",
    "you",
    "your",
    "with",
    "on",
    "that",
    "this",
    "it",
    "be",
    "as",
    "by",
    "can",
    "would",
    "should",
}


def tokens(text: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9+#]+", normalize(text)) if t and t not in _STOP}


def similar(a: str, b: str) -> bool:
    ta, tb = tokens(a), tokens(b)
    if ta and tb and len(ta & tb) / len(ta | tb) >= 0.75:
        return True
    return difflib.SequenceMatcher(None, normalize(a), normalize(b)).ratio() >= 0.9


def check_shape(q: GenQuestion) -> str | None:
    """Return a reason code if the question is malformed, else None."""
    if q.type == "mcq":
        opts = [o.strip() for o in q.options]
        if len(opts) != 4 or any(not o for o in opts):
            return "mcq_needs_four_options"
        if len({normalize(o) for o in opts}) != 4:
            return "duplicate_options"
        if q.correct_index is None or not 0 <= q.correct_index < 4:
            return "bad_answer_key"
        if any(any(v in normalize(o) for v in _VAGUE_OPTIONS) for o in opts):
            return "vague_option"
        if q.reference_points:
            return "mcq_with_reference_points"
    else:
        if q.options or q.correct_index is not None:
            return "short_answer_with_options"
        if len(q.reference_points) < 2 or any(len(p) < 10 for p in q.reference_points):
            return "short_answer_needs_reference_points"
    return None


def check_content(q: GenQuestion) -> str | None:
    """Reject text that links out, contains markup, tries to talk to the system, or claims to be a real company question."""
    blob = " ".join([q.prompt, q.explanation, *q.options, *q.reference_points])
    if _URL.search(blob) or _MARKUP.search(blob):
        return "url_or_markup"
    if injection_signals(blob):
        return "injection_text"
    if _FAKE_PROVENANCE.search(blob):
        return "claims_real_company_question"
    return None


def check_relevance(q: GenQuestion, context_skills: set[str], canon) -> str | None:
    if not ({canon(s) for s in q.skills} & context_skills):
        return "off_topic"
    return None


def check_evidence(q: GenQuestion, category: str, evidence_count: int) -> str | None:
    """Company-informed questions must point at evidence we actually provided; other categories must not claim any."""
    if category == "company_informed":
        if not q.informed_by or any(not 1 <= i <= evidence_count for i in q.informed_by):
            return "missing_or_invalid_evidence"
    elif q.informed_by:
        return "evidence_on_non_company_question"
    return None
