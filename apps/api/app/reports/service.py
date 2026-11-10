import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.companies import service as company_service
from app.core.config import get_settings
from app.core.errors import AppError, not_found
from app.core.ownership import get_owned_or_404
from app.core.rate_limit import report_limiter
from app.llm.base import LLMError
from app.llm.factory import get_llm_provider
from app.models.assessment import Assessment
from app.models.audit import record
from app.models.coding import CodingProblem, CodingSession
from app.models.interview import InterviewSession
from app.models.report import Report
from app.models.resume import Resume
from app.models.user import User
from app.reports import compute, roadmap
from app.reports.rubric import DISCLAIMER, RUBRIC, RUBRIC_VERSION
from app.reports.schemas import CreateReportIn, ReportOut, ReportSummary
from app.research import service as research
from app.resumes import roles
from app.resumes.schemas import ParsedResume

build_llm = get_llm_provider  # tests replace this hook
COMPARE_NOTE = "Each attempt uses different questions, so small changes are not meaningful."


def _role(slug: str) -> dict:
    r = next((r for r in roles.list_roles() if r["slug"] == slug), None)
    if r is None:
        raise not_found("Role")
    return {"slug": r["slug"], "title": r["title"]}


def _llm_or_none():
    try:
        return build_llm()
    except LLMError:
        return None  # a report never needs the AI: the plan falls back to a built-in one


def _coding_matches(db: Session, cs: CodingSession, role: str) -> bool:
    if (cs.plan or {}).get("role"):
        return cs.plan["role"] == role
    if cs.assessment_id:
        a = db.get(Assessment, cs.assessment_id)
        if a is not None:
            return a.role_slug == role
    for slug in cs.problem_slugs:
        p = db.scalars(select(CodingProblem).where(CodingProblem.slug == slug)).first()
        if p is not None and role in (p.roles or []):
            return True
    return False


def _company_sources(company, role_title: str) -> list[dict]:
    """The same rule as interviews and assessments: only active, non-outdated findings that match the role, each with its source URL and label."""
    items, seen = [], set()
    for f in research.active_findings(company):
        label = research.effective_label(f)
        if label == "unverified_or_outdated" or not research.title_matches(f.role_title, role_title) or f.source.url in seen:
            continue
        seen.add(f.source.url)
        items.append({"url": f.source.url, "label": label, "kind": f.kind, "role_title": f.role_title, "text": f.text[:240]})
    items.sort(key=lambda i: 0 if i["label"] == "official_verified" else 1)
    return items[:8]


def create(db: Session, user: User, data: CreateReportIn, auto: bool = False) -> Report:
    """auto=True: made by the app when the user finished a part of their practice. It never calls the AI and does not use the user's manual report quota."""
    cfg = get_settings()
    role = _role(data.role)
    if not (data.assessment_id or data.coding_session_id or data.interview_id):
        raise AppError(409, "nothing_to_report", "Choose at least one finished assessment, coding session or interview to build a report from.")
    a = c = iv = resume = None
    if data.assessment_id:
        a = get_owned_or_404(db, Assessment, data.assessment_id, user)
        if a.status != "submitted":
            raise AppError(409, "not_submitted", "Submit the assessment before using it in a report.")
        if a.role_slug != data.role:
            raise AppError(422, "role_mismatch", "That assessment is for a different role.")
    if data.coding_session_id:
        c = get_owned_or_404(db, CodingSession, data.coding_session_id, user)
        if c.status != "submitted":
            raise AppError(409, "not_submitted", "Finish the coding session before using it in a report.")
        if not _coding_matches(db, c, data.role):
            raise AppError(422, "role_mismatch", "That coding session is not for this role.")
    if data.interview_id:
        iv = get_owned_or_404(db, InterviewSession, data.interview_id, user)
        if iv.evaluation is None:
            raise AppError(409, "not_evaluated", "Get feedback on the interview before using it in a report.")
        if iv.role_slug != data.role:
            raise AppError(422, "role_mismatch", "That interview is for a different role.")
    parsed = None
    if data.resume_id:
        resume = get_owned_or_404(db, Resume, data.resume_id, user)
        if not resume.versions:
            raise AppError(409, "not_analyzed", "Analyse this resume first.")
        parsed = ParsedResume.model_validate(resume.versions[-1].parsed_json)
    if (db.scalar(select(func.count()).select_from(Report).where(Report.user_id == user.id, Report.auto.is_(False))) or 0) >= cfg.max_reports_per_user and not auto:  # automatic reports never use up the user's own quota
        raise AppError(409, "report_limit", f"You can keep up to {cfg.max_reports_per_user} reports. Delete an old one first.")
    wait = 0 if auto else report_limiter.retry_after(str(user.id), cfg.reports_per_hour, 3600)
    if wait:
        raise AppError(429, "rate_limited", "Too many reports created. Try again later.", headers={"Retry-After": str(wait)})

    res = compute.compute(db, compute.Inputs(role_slug=data.role, parsed=parsed, assessment=a, coding=c, interview=iv))
    notes = list(res["notes"])
    cids = [x.company_id for x in (a, iv) if x is not None]
    company = None
    if cids and all(cids) and len(set(cids)) == 1:
        company = company_service.get_by_id(db, cids[0])
    elif cids and any(cids):
        notes.append("The chosen results mix company-specific and general practice, so this report is general role preparation.")
    sources = _company_sources(company, role["title"]) if company is not None else []
    if company is not None and not sources:
        notes.append("No approved company evidence matches this role, so there are no company sources to show.")
    llm = None if auto else _llm_or_none()
    plan = roadmap.make(llm, res["gaps"], data.horizon, role["title"])
    if not auto:
        report_limiter.add(str(user.id))
    r = Report(
        auto=auto,
        user_id=user.id, role_slug=data.role, company_id=company.id if company else None, mode="company" if company else "general", resume_id=resume.id if resume else None,
        assessment_id=a.id if a else None, coding_session_id=c.id if c else None, interview_id=iv.id if iv else None, horizon=data.horizon, rubric_version=RUBRIC_VERSION, rubric=RUBRIC,
        components=res["components"], overall=res["overall"], gaps=res["gaps"], strengths=res["strengths"], practice_questions=res["practice_questions"], sources=sources, roadmap=plan,
        notes=notes, provider=llm.name if llm and plan["source"] == "ai" else "", model=llm.model if llm and plan["source"] == "ai" else "",
    )
    db.add(r)
    db.flush()
    record(db, "report_created", user.id, report_id=str(r.id), rubric=RUBRIC_VERSION)
    db.commit()
    return r


def regenerate_roadmap(db: Session, user: User, r: Report, horizon: int) -> Report:
    wait = report_limiter.retry_after(str(user.id), get_settings().reports_per_hour * 3, 3600)
    if wait:
        raise AppError(429, "rate_limited", "Too many requests. Try again later.", headers={"Retry-After": str(wait)})
    llm = _llm_or_none()
    plan = roadmap.make(llm, list(r.gaps), horizon, _role(r.role_slug)["title"])
    report_limiter.add(str(user.id) + ":roadmap")
    r.roadmap, r.horizon = plan, horizon  # only the plan changes; every score stays exactly as first computed
    r.provider, r.model = (llm.name, llm.model) if llm and plan["source"] == "ai" else ("", "")
    db.commit()
    return r


def get_owned(db: Session, report_id: uuid.UUID, user: User) -> Report:
    return get_owned_or_404(db, Report, report_id, user)


def _scores(r: Report) -> dict:
    return {c["key"]: c["value"] for c in r.components if c["status"] == "available"}


def previous_of(db: Session, r: Report) -> dict | None:
    p = db.scalars(select(Report).where(Report.user_id == r.user_id, Report.role_slug == r.role_slug, Report.created_at < r.created_at).order_by(Report.created_at.desc())).first()
    if p is None:
        return None
    now, before = _scores(r), _scores(p)
    deltas = [{"key": k, "before": before[k], "after": now[k], "delta": now[k] - before[k]} for k in now if k in before]
    ov = (p.overall or {}).get("value"), (r.overall or {}).get("value")
    return {"report_id": str(p.id), "created_at": p.created_at, "overall_before": ov[0], "overall_after": ov[1], "overall_delta": (ov[1] - ov[0]) if None not in ov else None, "components": deltas, "note": COMPARE_NOTE}


def out(db: Session, r: Report) -> ReportOut:
    company = None
    if r.company_id:
        c = company_service.get_by_id(db, r.company_id)
        company = {"slug": c.slug, "name": c.name} if c else None
    return ReportOut(
        id=r.id, created_at=r.created_at, role=_role(r.role_slug) if any(x["slug"] == r.role_slug for x in roles.list_roles()) else {"slug": r.role_slug, "title": r.role_slug},
        company=company, mode=r.mode, horizon=r.horizon, rubric_version=r.rubric_version, rubric=r.rubric,
        sources_used={"resume_id": str(r.resume_id) if r.resume_id else None, "assessment_id": str(r.assessment_id) if r.assessment_id else None, "coding_session_id": str(r.coding_session_id) if r.coding_session_id else None, "interview_id": str(r.interview_id) if r.interview_id else None},
        components=r.components, overall=r.overall, gaps=r.gaps, strengths=r.strengths, practice_questions=r.practice_questions, sources=r.sources, roadmap=r.roadmap, notes=r.notes,
        previous=previous_of(db, r), disclaimer=DISCLAIMER, provider=r.provider, model=r.model, auto=bool(r.auto),
    )


def summary(db: Session, r: Report) -> ReportSummary:
    company = None
    if r.company_id:
        c = company_service.get_by_id(db, r.company_id)
        company = {"slug": c.slug, "name": c.name} if c else None
    title = next((x["title"] for x in roles.list_roles() if x["slug"] == r.role_slug), r.role_slug)
    return ReportSummary(
        id=r.id, created_at=r.created_at, role={"slug": r.role_slug, "title": title}, company=company, mode=r.mode, horizon=r.horizon, overall=(r.overall or {}).get("value"), scores=_scores(r),
        included=list((r.overall or {}).get("included", [])), missing=[m["key"] for m in (r.overall or {}).get("missing", [])], auto=bool(r.auto),
    )


def progress(db: Session, user: User, role: str | None) -> dict:
    q = select(Report).where(Report.user_id == user.id).order_by(Report.created_at)
    if role:
        q = q.where(Report.role_slug == role)
    rows = db.scalars(q).all()
    series = [{"report_id": str(r.id), "created_at": r.created_at, "role": r.role_slug, "overall": (r.overall or {}).get("value"), "scores": _scores(r)} for r in rows]
    scored = [s for s in series if s["overall"] is not None]
    return {
        "series": series,
        "latest_change": (scored[-1]["overall"] - scored[-2]["overall"]) if len(scored) >= 2 else None,
        "note": "Each point comes from a stored report. Reports can use different components and different questions, so compare trends, not single points. These are preparation indicators.",
    }


def sources(db: Session, user: User, role: str) -> dict:
    _role(role)
    from app.assessments import service as asvc
    from app.coding import service as csvc

    assess = db.scalars(select(Assessment).where(Assessment.user_id == user.id, Assessment.status == "submitted", Assessment.role_slug == role).order_by(Assessment.created_at.desc()).limit(20)).all()
    sessions = db.scalars(select(CodingSession).where(CodingSession.user_id == user.id, CodingSession.status == "submitted").order_by(CodingSession.created_at.desc()).limit(40)).all()
    ivs = db.scalars(select(InterviewSession).where(InterviewSession.user_id == user.id, InterviewSession.role_slug == role).order_by(InterviewSession.created_at.desc()).limit(20)).all()
    resumes = db.scalars(select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())).all()
    coding_rows = []
    for s in sessions:
        if not _coding_matches(db, s, role):
            continue
        sm = csvc.session_summary(db, s)
        coding_rows.append({"id": str(s.id), "created_at": s.created_at, "problems": len(s.problem_slugs), "executed": sm.executed, "tests_passed": sm.tests_passed, "tests_total": sm.tests_total})
    return {
        "assessments": [{"id": str(a.id), "created_at": a.created_at, "mode": a.mode, "mcq_correct": asvc.result(a)["mcq_correct"], "mcq_total": asvc.result(a)["mcq_total"]} for a in assess],
        "coding_sessions": coding_rows[:20],
        "interviews": [{"id": str(i.id), "created_at": i.created_at, "answers_given": sum(1 for t in i.turns if t.kind == "answer") if i.transcript_purged_at is None else None, "evaluated": i.evaluation is not None, "indicator": (i.evaluation or {}).get("indicator")} for i in ivs if i.evaluation is not None],
        "resumes": [{"id": str(r.id), "filename": r.filename} for r in resumes if r.versions],
    }
