import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.companies import service as company_service
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError
from app.core.ownership import get_owned_or_404
from app.core.rate_limit import research_limiter
from app.discover import service
from app.models.resume import Resume
from app.models.user import User
from app.research import service as research
from app.research.provider import ResearchNotConfigured
from app.resumes.schemas import ParsedResume

router = APIRouter(prefix="/discover", tags=["discover"], dependencies=[Depends(get_current_user)])


@router.get("/recommendations")
def recommendations(
    resume_id: uuid.UUID,
    role: str | None = Query(default=None, max_length=80),
    q: str | None = Query(default=None, max_length=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    resume = get_owned_or_404(db, Resume, resume_id, user)
    if not resume.versions:
        raise AppError(409, "not_analyzed", "Analyse this resume first.")
    parsed = ParsedResume.model_validate(resume.versions[-1].parsed_json)
    return service.recommendations(db, parsed, role, q)


@router.get("/companies")
def companies(q: str | None = Query(default=None, max_length=100), family: str | None = Query(default=None, max_length=20), db: Session = Depends(get_db)):
    return {"items": service.list_all(db, q, family)}


@router.get("/companies/{slug}")
def company(slug: str, db: Session = Depends(get_db)):
    return service.detail(company_service.get_selectable_by_slug(db, slug))


@router.post("/companies/{slug}/research", status_code=202)
def start_research(slug: str, background: BackgroundTasks, force: bool = Query(default=False), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    c = company_service.get_selectable_by_slug(db, slug)
    try:
        research.build_research()
    except ResearchNotConfigured:
        raise AppError(503, "research_not_configured", "Live research isn't set up (add TAVILY_API_KEY to apps/api/.env and restart the API).") from None
    run, cached = research.start_run(db, c, user, force, auto=True)
    if cached:
        db.commit()
        return {"id": str(run.id), "status": run.status, "cached": True, "summary": run.summary or {}}
    s = get_settings()
    wait = research_limiter.retry_after(str(user.id), s.research_runs_per_hour, 3600)
    if wait:
        db.rollback()
        raise AppError(429, "rate_limited", "Too many research runs. Try again later.", headers={"Retry-After": str(wait)})
    research_limiter.add(str(user.id))
    db.commit()
    background.add_task(research.execute_run, run.id, True)
    return {"id": str(run.id), "status": run.status, "cached": False, "summary": {}}


@router.get("/companies/{slug}/research")
def research_status(slug: str, db: Session = Depends(get_db)):
    c = company_service.get_selectable_by_slug(db, slug)
    return service.detail(c)
