"""Chooses coding problems that fit a software house's practice emphasis and the candidate's resume.

HONESTY NOTE: nobody publishes the questions a company asks, and this project has not verified any. A "company focus" here is the
project's own rough tech-focus note for that company (data/company_seed) turned into problem tags (data/company_focus/focus.json).
It shapes WHICH practice problems you get. It is never presented as a real company question."""

import json
from collections import Counter
from functools import lru_cache
from pathlib import Path

from app.resumes import roles
from app.resumes.schemas import ParsedResume

ROOT = Path(__file__).resolve().parents[4]
FOCUS_FILE = ROOT / "data" / "company_focus" / "focus.json"
SEED_FILE = ROOT / "data" / "company_seed" / "lahore_candidates.json"
LABEL = "practice_focus_not_verified"
DISCLAIMER = "Practice emphasis based on the company's rough tech focus in this project. These are not the company's real interview questions."

TAG_TITLES = {
    "basics": "core loops and conditions", "strings": "string handling", "hashing": "dictionaries and sets", "grouping": "grouping and counting with dicts",
    "sorting": "sorting and ordering", "set-ops": "set operations", "business-rules": "business rules with conditions", "fintech": "money and ledger logic",
    "api-logic": "backend / API style logic", "data-cleaning": "data cleaning", "math-basics": "number logic", "matrix": "2D lists",
    "simulation": "step-by-step simulation", "security": "security-style checks", "recursion": "recursion and nesting", "stacks": "stacks", "searching": "searching",
    "trees": "trees", "linked-lists": "linked lists", "dp": "dynamic programming", "graphs": "graphs and BFS", "two-pointers": "two pointers", "backtracking": "backtracking",
}


@lru_cache
def _cfg() -> dict:
    return json.loads(FOCUS_FILE.read_text(encoding="utf-8"))


@lru_cache
def _seed() -> list[dict]:
    return json.loads(SEED_FILE.read_text(encoding="utf-8"))["companies"]


def _weights(keys: list[str], table: dict) -> Counter:
    c: Counter = Counter()
    for k in keys:
        for rank, tag in enumerate(table.get(k.strip().lower(), [])):
            c[tag] += 3 - rank if rank < 3 else 1  # the first tag of a technology matters most
    return c


def company_profiles() -> list[dict]:
    out = []
    for c in _seed():
        w = _weights(c.get("tech_focus", []), _cfg()["tech_to_tags"])
        top = [t for t, _ in w.most_common(5)]
        out.append({"slug": c["slug"], "name": c["name"], "tech_focus": c.get("tech_focus", []), "focus_tags": top, "focus": [TAG_TITLES.get(t, t) for t in top[:4]], "label": LABEL})
    return out


def company_profile(slug: str) -> dict | None:
    return next((p for p in company_profiles() if p["slug"] == slug), None)


def company_weights(slug: str | None) -> Counter:
    if not slug:
        return Counter()
    c = next((x for x in _seed() if x["slug"] == slug), None)
    return _weights(c.get("tech_focus", []), _cfg()["tech_to_tags"]) if c else Counter()


# ---------------------------------------------------------------- resume
def resume_profile(parsed: ParsedResume | None) -> dict:
    """What the resume says about languages and skills, turned into problem tags and a language to practise in."""
    if parsed is None:
        return {"languages": [], "language": "python", "language_note": None, "skills": [], "tags": Counter(), "tag_names": []}
    have = roles._resume_skills(parsed)
    cfg = _cfg()
    skills = sorted(have)
    languages = [s.name.strip().lower() for s in parsed.skills if s.category == "language"] + [k for k in skills if k in cfg["languages"]["known"]]
    languages = list(dict.fromkeys(roles.canon(x) for x in languages))
    tags = _weights(skills, cfg["skill_to_tags"])
    executable = cfg["languages"]["executable"]
    usable = next((x for x in languages if x in executable), None)
    if usable:
        language, note = usable, None
    elif languages:
        language = "python"
        note = f"Your resume lists {', '.join(languages[:3])}. The code runner can run {', '.join(x.title() for x in executable)} for now, so these problems use Python. The logic carries over to your language."
    else:
        language, note = "python", "No programming language was found on your resume, so these problems use Python."
    return {"languages": languages, "language": language, "language_note": note, "skills": skills[:25], "tags": tags, "tag_names": [t for t, _ in tags.most_common(5)]}


# ---------------------------------------------------------------- ranking
def score(problem, company_w: Counter, resume_w: Counter) -> tuple[float, list[str]]:
    """Higher is a better fit. Returns the score and the tags that explain it."""
    tags = set(problem.tags or [])
    s, why = 0.0, []
    for t in tags:
        gain = company_w.get(t, 0) * 1.0 + resume_w.get(t, 0) * 0.7
        if gain:
            s += gain
            why.append(t)
    structures = len(set(problem.ds or []) & {"list", "tuple", "dict", "set"})
    s += 0.4 * structures  # screening rounds like problems that combine several structures
    return s, sorted(why, key=lambda t: -(company_w.get(t, 0) + resume_w.get(t, 0)))


def reason(problem, company_name: str | None, resume_w: Counter, why: list[str]) -> str:
    parts = []
    focus = [TAG_TITLES.get(t, t) for t in why[:2]]
    if company_name and focus:
        parts.append(f"{company_name} practice focus: {', '.join(focus)}")
    elif focus:
        parts.append(f"Matches your resume skills: {', '.join(focus)}")
    ds = [x for x in (problem.ds or []) if x in ("list", "tuple", "dict", "set")]
    if len(ds) >= 2:
        parts.append("combines " + " + ".join(ds))
    return "; ".join(parts) or "General practice for this role"


# ---------------------------------------------------------------- a company's fixed practice set
QUOTA = {"easy": 10, "medium": 10, "hard": 5}


def company_set(problems: list, slug: str, role: str | None = None) -> list[tuple]:
    """The 25-problem practice set for a company: 10 easy, 10 medium and 5 hard problems, those that fit its practice focus best.
    The same inputs always give the same set. Returns (problem, tags that explain the fit) ordered easy, medium, hard."""
    pool = [p for p in problems if not role or role in p.roles]
    cw = company_weights(slug)
    ranked = sorted(pool, key=lambda p: (-score(p, cw, Counter())[0], p.slug))
    chosen: list = []
    for level, n in QUOTA.items():
        chosen += [p for p in ranked if p.difficulty == level][:n]
    if len(chosen) < sum(QUOTA.values()):  # a level has too few problems: fill up with the best remaining ones
        chosen += [p for p in ranked if p not in chosen][: sum(QUOTA.values()) - len(chosen)]
    order = {"easy": 0, "medium": 1, "hard": 2}
    chosen.sort(key=lambda p: (order[p.difficulty], -score(p, cw, Counter())[0], p.slug))
    return [(p, score(p, cw, Counter())[1]) for p in chosen]
