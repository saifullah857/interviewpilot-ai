"""Company readiness and match scores.

Everything here is a plain calculation over the user's own saved results and the project's rough company focus notes.
Nothing is estimated by an AI, nothing is hard-coded per company, and a part with no evidence is shown as "not assessed"
and left out of the score instead of being guessed. The result is a preparation estimate, never a hiring probability."""

from collections import Counter, defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.coding import focus
from app.core.errors import not_found
from app.models.coding import CodingProblem
from app.models.question import BankQuestion
from app.models.resume import Resume
from app.models.screening import ScreeningSession
from app.models.user import User
from app.reports import auto as report_auto
from app.reports import compute as rc
from app.resumes import roles
from app.resumes.schemas import ParsedResume

DISCLAIMER = "This is an internal preparation estimate based on your own results and rough company focus notes. It is not a hiring probability and not a promise of selection."
WEIGHTS = {"skill_match": 15, "role_relevance": 10, "screening": 20, "technical_knowledge": 15, "coding_correctness": 25, "interview_performance": 15}
NAMES = {
    "skill_match": "Skill match",
    "role_relevance": "Role relevance for this company",
    "screening": "Online screening",
    "technical_knowledge": "Technical assessment",
    "coding_correctness": "Coding",
    "interview_performance": "Technical interview",
}
HOW = {
    "skill_match": "Share of the role's required skills (counted twice) and preferred skills that your resume states. Skills the AI only inferred count half. Skills linked to the company's focus count 1.5 times.",
    "role_relevance": "How much of the company's focus areas this role's skills cover (overlap of two distributions from the project's focus notes, unverified).",
    "screening": "Average score of your last 3 finished online screening tests for this role.",
    "technical_knowledge": "Your latest submitted assessment for this role, objective questions only.",
    "coding_correctness": "Share of tests passed in your latest finished coding session for this role (only code that really ran).",
    "interview_performance": "Your latest evaluated mock interview for this role.",
}
EVIDENCE = ("screening", "technical_knowledge", "coding_correctness", "interview_performance")
SKILL_CATEGORY = {
    "python": "python", "sql": "sql", "javascript": "javascript", "typescript": "javascript", "react": "react", "git": "git", "rest api": "rest", "testing": "qa",
    "machine learning": "ml", "deep learning": "ml", "statistics": "ml", "scikit-learn": "ml", "nlp": "nlp", "llm": "llm", "rag": "llm",
    "docker": "cloud", "aws": "cloud", "cloud": "cloud", "linux": "os", "operating systems": "os", "networking": "networks", "oop": "oop",
    "data structures": "dsa", "algorithms": "dsa", "java": "oop", "c#": "oop", ".net": "oop", "unity": "game",
}
LABELS = [(75, "Strong match"), (60, "Good match"), (40, "Needs improvement"), (0, "Low match")]


def label(value: int) -> str:
    return next(t for floor, t in LABELS if value >= floor)


def _catalog_role(slug: str) -> dict:
    r = next((x for x in roles._catalog()["roles"] if x["slug"] == slug), None)
    if r is None:
        raise not_found("Role")
    return r


def parsed_resume(db: Session, user: User, resume_id) -> tuple[ParsedResume | None, Resume | None]:
    if resume_id:
        from app.core.ownership import get_owned_or_404

        r = get_owned_or_404(db, Resume, resume_id, user)
    else:
        r = next((x for x in db.scalars(select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())).all() if x.versions), None)
    if r is None or not r.versions:
        return None, r
    return ParsedResume.model_validate(r.versions[-1].parsed_json), r


def _dist(c: Counter) -> dict[str, float]:
    total = sum(c.values())
    return {k: v / total for k, v in c.items()} if total else {}


def role_relevance(role: dict, company_slug: str | None) -> int | None:
    cw = focus.company_weights(company_slug)
    if not cw:
        return None
    rw = focus._weights([*role["required"], *role["preferred"]], focus._cfg()["skill_to_tags"])
    pc, pr = _dist(cw), _dist(rw)
    return round(100 * sum(min(pc[t], pr.get(t, 0)) for t in pc))


def skill_match(role: dict, parsed: ParsedResume, company_slug: str | None) -> dict:
    have = roles._resume_skills(parsed)
    table = focus._cfg()["skill_to_tags"]
    top = set(dict(focus.company_weights(company_slug).most_common(5))) if company_slug else set()
    got = tot = 0.0
    matched, missing = [], []
    for skills, base in ((role["required"], 2.0), (role["preferred"], 1.0)):
        for s in skills:
            w = base * (1.5 if top & set(table.get(roles.canon(s), [])) else 1.0)
            tot += w
            h = have.get(roles.canon(s))
            if h:
                got += w * (1.0 if h[0] == "stated" else 0.5)
                matched.append({"skill": s, "source": h[0], "required": s in role["required"]})
            else:
                missing.append({"skill": s, "required": s in role["required"]})
    return {"value": round(100 * got / tot) if tot else None, "matched": matched, "missing": missing}


def _screening(db: Session, user: User, role_slug: str) -> tuple[int | None, int]:
    rows = db.scalars(select(ScreeningSession).where(ScreeningSession.user_id == user.id, ScreeningSession.status == "submitted", ScreeningSession.role_slug == role_slug).order_by(ScreeningSession.submitted_at.desc()).limit(3)).all()
    scores = [r.score for r in rows if r.score is not None]
    return (round(sum(scores) / len(scores)), len(scores)) if scores else (None, 0)


def category_evidence(db: Session, user: User) -> dict[str, dict]:
    """Correct answers per screening topic over all of the user's finished tests."""
    agg: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for r in db.scalars(select(ScreeningSession).where(ScreeningSession.user_id == user.id, ScreeningSession.status == "submitted")).all():
        for c in (r.result or {}).get("by_category", []):
            agg[c["name"]][0] += c["correct"]
            agg[c["name"]][1] += c["total"]
    return {k: {"correct": v[0], "total": v[1], "score": round(v[0] / v[1] * 100)} for k, v in agg.items() if v[1]}


def _coding_average(db: Session, user: User) -> int | None:
    from app.reports.dashboard import build

    scores = [c["score"] for c in build(db, user)["coding"] if c["score"] is not None]
    return round(sum(scores) / len(scores)) if scores else None


def evaluate(db: Session, user: User, role_slug: str, company_slug: str | None, parsed: ParsedResume | None) -> dict:
    role = _catalog_role(role_slug)
    comps: dict[str, dict] = {}

    def put(key: str, value: int | None, reason: str = "", detail: dict | None = None, n: int = 0):
        comps[key] = {"key": key, "name": NAMES[key], "weight": WEIGHTS[key], "how": HOW[key], "status": "available" if value is not None else "not_assessed", "value": value, "reason": reason, "detail": detail or {}, "evidence_count": n}

    sm = skill_match(role, parsed, company_slug) if parsed is not None else None
    put("skill_match", sm["value"] if sm else None, "" if sm else "Analyse a resume first.", {"matched": sm["matched"], "missing": sm["missing"]} if sm else {})
    rr = role_relevance(role, company_slug)
    put("role_relevance", rr, "" if rr is not None else "Choose a company to see this.")
    sv, sn = _screening(db, user, role_slug)
    put("screening", sv, "" if sv is not None else "No finished screening test for this role yet.", n=sn)
    a, c, iv = report_auto._latest_assessment(db, user.id, role_slug), report_auto._latest_coding(db, user.id, role_slug), report_auto._latest_interview(db, user.id, role_slug)
    base = {x["key"]: x for x in rc.compute(db, rc.Inputs(role_slug=role_slug, parsed=None, assessment=a, coding=c, interview=iv))["components"]}
    for key in ("technical_knowledge", "coding_correctness", "interview_performance"):
        b = base[key]
        put(key, b["value"] if b["status"] == "available" else None, b.get("reason", "") if b["status"] != "available" else "", n=1 if b["status"] == "available" else 0)
    ordered = [comps[k] for k in WEIGHTS]
    avail = [x for x in ordered if x["value"] is not None]
    wsum = sum(x["weight"] for x in avail)
    for x in ordered:
        x["effective_weight"] = round(100 * x["weight"] / wsum) if x["value"] is not None and wsum else 0
    value = round(sum(x["value"] * x["weight"] for x in avail) / wsum) if wsum else None
    ev = sum(1 for k in EVIDENCE if comps[k]["value"] is not None)
    if ev == 0 and comps["skill_match"]["value"] is None:
        value = None  # company relevance alone says nothing about this person
    conf = {0: "resume_only", 1: "limited", 2: "moderate"}.get(ev, "good")
    return {
        "role": {"slug": role["slug"], "title": role["title"]}, "components": ordered, "evidence_count": ev,
        "overall": {"value": value, "label": "Not enough data" if value is None else label(value) if ev else "Resume-based estimate only", "confidence": conf,
                    "explanation": "Weighted average of the parts that have data. Parts marked not assessed are left out and the weights of the others are scaled up to 100%."},
        "skill_match": sm,
    }
