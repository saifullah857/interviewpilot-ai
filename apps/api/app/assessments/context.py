"""Builds the facts an assessment is written from: the role, what the resume shows, approved company evidence, and the user's history."""

from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.company import Company
from app.research import service as research
from app.resumes import roles
from app.resumes.schemas import ParsedResume


@dataclass
class Context:
    role: dict
    level: str
    required: list[str]
    preferred: list[str]
    resume_skills: list[dict]
    projects: list[dict]
    experience: list[dict]
    missing: list[str]
    evidence: list[dict] = field(default_factory=list)  # numbered from 1
    company_name: str | None = None
    focus_topics: list[str] = field(default_factory=list)
    prior_prompts: list[str] = field(default_factory=list)
    context_skills: set[str] = field(default_factory=set)


def level_for(title: str) -> str:
    t = title.lower()
    return "intern" if "intern" in t else "junior" if "junior" in t else "entry-level"


def weak_topics(db: Session, user_id, limit_assessments: int = 3) -> list[str]:
    """Topics where the user got fewer than half the multiple-choice questions right (at least 2 questions) in recent submitted tests."""
    rows = db.scalars(
        select(Assessment).where(Assessment.user_id == user_id, Assessment.status == "submitted").order_by(Assessment.submitted_at.desc()).limit(limit_assessments)
    ).all()
    tally: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for a in rows:
        correct = {x.question_id: x.is_correct for x in a.answers}
        for q in a.questions:
            if q.type == "mcq":
                tally[q.topic][1] += 1
                tally[q.topic][0] += 1 if correct.get(q.id) else 0
    return sorted(t for t, (ok, n) in tally.items() if n >= 2 and ok / n < 0.5)


def prior_prompts(db: Session, user_id, limit: int = 80) -> list[str]:
    rows = db.scalars(
        select(Assessment)
        .where(Assessment.user_id == user_id, Assessment.status.in_(("ready", "in_progress", "submitted")))
        .order_by(Assessment.created_at.desc())
        .limit(5)
    ).all()
    return [q.prompt for a in rows for q in a.questions][:limit]


def build(db: Session, user_id, parsed: ParsedResume, role_slug: str, company: Company | None) -> Context:
    cat = roles._catalog()
    role = next(r for r in cat["roles"] if r["slug"] == role_slug)
    have = roles._resume_skills(parsed)
    # within each list, skills the resume does not show come first, then AI-inferred ones, then stated ones: practice goes where it is needed
    rank = {None: 0, "inferred": 1, "stated": 2}

    def order(skills: list[str]) -> list[str]:
        return sorted(skills, key=lambda s: rank[have[roles.canon(s)][0]] if roles.canon(s) in have else 0)

    required, preferred = order(list(role["required"])), order(list(role["preferred"]))
    ctx = Context(
        role={"slug": role["slug"], "title": role["title"]},
        level=level_for(role["title"]),
        required=required,
        preferred=preferred,
        resume_skills=[{"name": s.name, "source": s.source} for s in parsed.skills],
        projects=[{"name": p.name, "description": p.description, "technologies": p.technologies} for p in parsed.projects],
        experience=[{"title": e.title, "organization": e.organization, "summary": e.summary, "technologies": e.technologies} for e in parsed.experience],
        missing=[s for s in required + preferred if roles.canon(s) not in have],
        focus_topics=weak_topics(db, user_id),
        prior_prompts=prior_prompts(db, user_id),
    )
    if company is not None:
        ctx.company_name = company.name
        items = []
        for f in research.active_findings(company):
            label = research.effective_label(f)
            if label == "unverified_or_outdated" or not research.title_matches(f.role_title, role["title"]):
                continue  # outdated or unrelated evidence never inspires a question
            items.append(
                {"label": label, "kind": f.kind, "role_title": f.role_title, "text": f.text, "skills": list(f.skills or []), "finding_id": str(f.id), "url": f.source.url}
            )
        items.sort(key=lambda i: 0 if i["label"] == "official_verified" else 1)
        ctx.evidence = [{"n": n, **item} for n, item in enumerate(items[:12], start=1)]
    skills = {roles.canon(s) for s in required + preferred} | {roles.canon(s["name"]) for s in ctx.resume_skills}
    for e in ctx.evidence:
        skills |= {roles.canon(s) for s in e["skills"]}
    ctx.context_skills = {s for s in skills if s}
    return ctx
