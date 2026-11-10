"""Reports that make themselves. When a user finishes a coding session, submits an assessment or gets interview feedback, the app builds
(or upgrades) a report from the latest finished work for that role and saves it in their history. It never calls the AI (the plan is the
built-in one; the user can ask for an AI-written plan later) and it can never break the action that triggered it."""

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assessment import Assessment
from app.models.coding import CodingSession
from app.models.interview import InterviewSession
from app.models.report import Report
from app.models.resume import Resume

log = logging.getLogger("interviewpilot.reports")
MAX_AUTO = 40


def _coding_role(db: Session, cs: CodingSession) -> str | None:
    if (cs.plan or {}).get("role"):
        return cs.plan["role"]
    if cs.assessment_id:
        a = db.get(Assessment, cs.assessment_id)
        if a is not None:
            return a.role_slug
    return None


def _latest_assessment(db: Session, user_id, role: str) -> Assessment | None:
    return db.scalars(select(Assessment).where(Assessment.user_id == user_id, Assessment.status == "submitted", Assessment.role_slug == role).order_by(Assessment.submitted_at.desc())).first()


def _latest_coding(db: Session, user_id, role: str) -> CodingSession | None:
    rows = db.scalars(select(CodingSession).where(CodingSession.user_id == user_id, CodingSession.status == "submitted").order_by(CodingSession.submitted_at.desc()).limit(15)).all()
    return next((c for c in rows if _coding_role(db, c) == role), None)


def _latest_interview(db: Session, user_id, role: str) -> InterviewSession | None:
    rows = db.scalars(select(InterviewSession).where(InterviewSession.user_id == user_id, InterviewSession.role_slug == role).order_by(InterviewSession.created_at.desc()).limit(15)).all()
    return next((i for i in rows if i.evaluation), None)


def make(db: Session, user_id, role: str, a: Assessment | None = None, c: CodingSession | None = None, iv: InterviewSession | None = None) -> Report | None:
    from app.core.db import utcnow  # noqa: F401
    from app.models.user import User
    from app.reports import service
    from app.reports.schemas import CreateReportIn

    a = a or _latest_assessment(db, user_id, role)
    c = c or _latest_coding(db, user_id, role)
    iv = iv or _latest_interview(db, user_id, role)
    if not (a or c or iv):
        return None
    ids = (a.id if a else None, c.id if c else None, iv.id if iv else None)
    mine = db.scalars(select(Report).where(Report.user_id == user_id)).all()
    for r in mine:
        if (r.assessment_id, r.coding_session_id, r.interview_id) == ids:
            return r  # this exact combination already has a report
    resume_id = (c.resume_id if c else None) or (a.resume_id if a else None)
    if resume_id is None:
        resume_id = next((x.id for x in db.scalars(select(Resume).where(Resume.user_id == user_id).order_by(Resume.created_at.desc())).all() if x.versions), None)
    user = db.get(User, user_id)
    report = service.create(db, user, CreateReportIn(role=role, resume_id=resume_id, assessment_id=ids[0], coding_session_id=ids[1], interview_id=ids[2], horizon=7), auto=True)
    # an automatic report that only held part of this work is replaced by the fuller one
    new = {x for x in ids if x}
    for r in mine:
        old = {x for x in (r.assessment_id, r.coding_session_id, r.interview_id) if x}
        if r.auto and r.role_slug == role and old and old < new:
            db.delete(r)
    autos = [r for r in db.scalars(select(Report).where(Report.user_id == user_id, Report.auto.is_(True)).order_by(Report.created_at.desc())).all()]
    for r in autos[MAX_AUTO:]:  # keep the history tidy: only the newest automatic reports are kept
        db.delete(r)
    db.commit()
    return report


def _safe(db: Session, fn) -> None:
    try:
        fn()
    except Exception:  # noqa: BLE001 - a report must never break finishing a session
        db.rollback()
        log.warning("automatic report was not created", exc_info=True)


def after_coding(db: Session, cs: CodingSession) -> None:
    role = _coding_role(db, cs)
    if role:
        _safe(db, lambda: make(db, cs.user_id, role, a=db.get(Assessment, cs.assessment_id) if cs.assessment_id else None, c=cs))


def after_assessment(db: Session, a: Assessment) -> None:
    _safe(db, lambda: make(db, a.user_id, a.role_slug, a=a))


def after_interview(db: Session, iv: InterviewSession) -> None:
    if iv.evaluation:
        _safe(db, lambda: make(db, iv.user_id, iv.role_slug, iv=iv))
