import random
import uuid
from collections import defaultdict
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.coding import focus
from app.core.db import utcnow
from app.core.errors import AppError, not_found
from app.models.audit import record
from app.models.question import BankQuestion
from app.models.screening import ScreeningSession
from app.models.user import User
from app.questions import service as qs
from app.resumes import roles
from app.screening.schemas import AnswerIn, CreateScreeningIn, ReviewItem, ScreeningOut, ScreeningResult, ScreeningSummary

NOTE = "Scored by fixed rules: one point per correct answer. This is a preparation indicator, not a prediction of any company's hiring decision."
ORDER = ["easy", "medium", "hard"]


def _company(slug: str | None) -> dict | None:
    p = focus.company_profile(slug) if slug else None
    return {"slug": p["slug"], "name": p["name"]} if p else None


def _questions(db: Session, slugs: list[str]) -> dict[str, BankQuestion]:
    rows = db.scalars(select(BankQuestion).where(BankQuestion.slug.in_(slugs))).all()
    return {r.slug: r for r in rows}


def _pick(db: Session, user: User, data: CreateScreeningIn) -> list[BankQuestion]:
    pool = [q for q in db.scalars(select(BankQuestion).where(BankQuestion.enabled.is_(True), BankQuestion.kind.in_(["mcq", "output"]))).all() if data.role in q.roles and (not data.company or data.company in q.companies)]
    if len(pool) < 5:
        raise AppError(409, "not_enough_questions", "There are not enough screening questions for this company and role yet. Try another role or leave the company empty.")
    recent = db.scalars(select(ScreeningSession).where(ScreeningSession.user_id == user.id).order_by(ScreeningSession.created_at.desc()).limit(5)).all()
    seen = {s for r in recent for s in r.question_slugs}
    rng = random.Random(uuid.uuid4().int)  # noqa: S311 - variety, not security
    count = min(data.count, len(pool))
    if data.level == "mixed":
        want = {"easy": round(count * 0.4), "medium": round(count * 0.4)}
        want["hard"] = count - want["easy"] - want["medium"]
    else:
        want = {data.level: count}
    chosen: list[BankQuestion] = []
    for level, n in want.items():
        pick_from = [q for q in pool if q.difficulty == level and q not in chosen]
        chosen += _spread(pick_from, n, seen, rng)
    if len(chosen) < count:  # top up from any level when one level has too few questions
        chosen += _spread([q for q in pool if q not in chosen], count - len(chosen), seen, rng)
    rng.shuffle(chosen)
    return chosen


def _spread(pool: list[BankQuestion], n: int, seen: set[str], rng: random.Random) -> list[BankQuestion]:
    """Takes n questions, unseen first, spread over the categories so one topic does not dominate."""
    by: dict[str, list[BankQuestion]] = defaultdict(list)
    rng.shuffle(pool)
    pool.sort(key=lambda q: q.slug in seen)
    for q in pool:
        by[q.category].append(q)
    out: list[BankQuestion] = []
    cats = list(by)
    rng.shuffle(cats)
    while len(out) < n and any(by.values()):
        for c in cats:
            if by[c] and len(out) < n:
                out.append(by[c].pop(0))
    return out


def create(db: Session, user: User, data: CreateScreeningIn) -> ScreeningSession:
    if data.role not in qs.valid_roles():
        raise not_found("Role")
    if data.company and focus.company_profile(data.company) is None:
        raise not_found("Company")
    for s in db.scalars(select(ScreeningSession).where(ScreeningSession.user_id == user.id, ScreeningSession.status == "in_progress")).all():
        refresh(db, s)
        if s.status == "in_progress":
            raise AppError(409, "active_session", "You already have a screening test in progress. Finish it first.")
    qsel = _pick(db, user, data)
    now = utcnow()
    s = ScreeningSession(user_id=user.id, company_slug=data.company, role_slug=data.role, level=data.level, question_slugs=[q.slug for q in qsel], answers={}, status="in_progress", started_at=now, deadline_at=now + timedelta(minutes=max(10, round(len(qsel) * 1.5))), total=len(qsel), result={})
    db.add(s)
    record(db, "screening_started", user.id, session_id=str(s.id), company=data.company, role=data.role)
    db.commit()
    return s


def refresh(db: Session, s: ScreeningSession) -> None:
    if s.status == "in_progress" and utcnow() >= s.deadline_at:
        submit(db, s, auto=True)


def out(db: Session, s: ScreeningSession) -> ScreeningOut:
    qmap = _questions(db, s.question_slugs)
    return ScreeningOut(id=s.id, status=s.status, company=_company(s.company_slug), role=s.role_slug, level=s.level, started_at=s.started_at, deadline_at=s.deadline_at, server_now=utcnow(), total=s.total, answered=len(s.answers or {}), questions=[qs.public(qmap[x]) for x in s.question_slugs if x in qmap], answers={k: int(v) for k, v in (s.answers or {}).items()})


def summary(s: ScreeningSession) -> ScreeningSummary:
    return ScreeningSummary(id=s.id, status=s.status, company=_company(s.company_slug), role=s.role_slug, level=s.level, submitted_at=s.submitted_at, correct=s.correct, total=s.total, score=s.score)


def answer(db: Session, s: ScreeningSession, data: AnswerIn) -> ScreeningOut:
    refresh(db, s)
    if s.status != "in_progress":
        raise AppError(409, "session_finished", "This test is finished, answers can no longer be changed.")
    if data.question not in s.question_slugs:
        raise not_found("Question")
    q = _questions(db, [data.question])[data.question]
    answers = dict(s.answers or {})
    if data.choice is None:
        answers.pop(data.question, None)
    else:
        if data.choice >= len(q.options):
            raise AppError(422, "invalid_choice", "That option does not exist.")
        answers[data.question] = data.choice
    s.answers = answers
    db.commit()
    return out(db, s)


def _pct(c: int, t: int) -> int:
    return round(c / t * 100) if t else 0


def advice(score: int, level: str, cats: list[dict]) -> dict:
    """Deterministic next step: nothing here is written by an AI."""
    low = sorted((c for c in cats if c["score"] < 50), key=lambda c: (c["score"], -c["total"]))
    weak = [c["name"] for c in low if c["total"] >= 2][:3] or [c["name"] for c in low][:3]  # a topic with a single question counts only when nothing larger is weak
    strong = [c["name"] for c in cats if c["total"] >= 2 and c["score"] >= 80][:3]
    cur = ORDER.index(level) if level in ORDER else 1
    if score >= 80:
        nxt = ORDER[min(cur + 1, 2)] if level != "mixed" else "hard"
        msg = f"Strong result. Try {nxt} questions next."
    elif score <= 40:
        nxt = ORDER[max(cur - 1, 0)] if level != "mixed" else "easy"
        msg = f"Build the basics first with {nxt} questions" + (f", starting with {', '.join(weak)}." if weak else ".")
    else:
        nxt = level
        msg = "Keep practising at this level" + (f" and focus on {', '.join(weak)}." if weak else ".")
    return {"next_level": nxt, "weak_categories": weak, "strong_categories": strong, "message": msg}


def submit(db: Session, s: ScreeningSession, auto: bool = False) -> ScreeningSession:
    if s.status == "submitted":
        return s
    qmap = _questions(db, s.question_slugs)
    cat: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    dif: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    correct = 0
    for slug in s.question_slugs:
        q = qmap.get(slug)
        if q is None:
            continue
        ok = (s.answers or {}).get(slug) == q.answer_index
        correct += ok
        for d, key in ((cat, q.category), (dif, q.difficulty)):
            d[key][1] += 1
            d[key][0] += ok
    cats = [{"name": k, "correct": v[0], "total": v[1], "score": _pct(*v)} for k, v in sorted(cat.items())]
    difs = [{"name": k, "correct": v[0], "total": v[1], "score": _pct(*v)} for k, v in sorted(dif.items(), key=lambda kv: ORDER.index(kv[0]))]
    total = s.total or len(s.question_slugs)
    s.correct, s.score, s.status, s.submitted_at, s.auto_submitted = correct, _pct(correct, total), "submitted", utcnow(), auto
    s.result = {"by_category": cats, "by_difficulty": difs, "next_step": advice(s.score, s.level, cats)}
    record(db, "screening_submitted", s.user_id, session_id=str(s.id), score=s.score, auto=auto)
    db.commit()
    return s


def result(db: Session, s: ScreeningSession) -> ScreeningResult:
    qmap = _questions(db, s.question_slugs)
    review = []
    for slug in s.question_slugs:
        q = qmap.get(slug)
        if q is None:
            continue
        chosen = (s.answers or {}).get(slug)
        review.append(ReviewItem(slug=slug, category=q.category, difficulty=q.difficulty, kind=q.kind, prompt=q.prompt, options=list(q.options), chosen=chosen, answer_index=q.answer_index or 0, correct=chosen == q.answer_index, explanation=q.explanation))
    r = s.result or {}
    return ScreeningResult(session=summary(s), auto_submitted=bool(s.auto_submitted), by_category=r.get("by_category", []), by_difficulty=r.get("by_difficulty", []), next_step=r.get("next_step", {}), review=review, note=NOTE)
