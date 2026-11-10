import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from app.auth.deps import require_admin
from app.companies import mapping, service
from app.companies.schemas import AdminCompanyDetail
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError
from app.core.rate_limit import research_limiter
from app.models.user import User
from app.research import service as research
from app.research.provider import ResearchNotConfigured
from app.research.schemas import FindingStatusIn, RunOut

router = APIRouter(prefix="/admin/companies", tags=["research"])


def _run_out(r, cached: bool = False) -> RunOut:
    return RunOut(id=r.id, status=r.status, error_code=r.error_code, summary=r.summary or {}, started_at=r.started_at, finished_at=r.finished_at, cached=cached)


@router.post("/{company_id}/research", response_model=RunOut, status_code=202)
def start_research(
    company_id: uuid.UUID,
    background: BackgroundTasks,
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    company = service.get_by_id(db, company_id)
    try:
        research.build_research()  # fail early and clearly if no search key is configured
    except ResearchNotConfigured:
        raise AppError(503, "research_not_configured", "Live research isn't set up on this server (no search key).") from None
    run, cached = research.start_run(db, company, user, force)
    if cached:
        db.commit()
        return _run_out(run, cached=True)
    s = get_settings()
    wait = research_limiter.retry_after(str(user.id), s.research_runs_per_hour, 3600)
    if wait:
        db.rollback()
        raise AppError(429, "rate_limited", "Too many research runs. Try again later.", headers={"Retry-After": str(wait)})
    research_limiter.add(str(user.id))
    db.commit()
    background.add_task(research.execute_run, run.id)
    return _run_out(run)


@router.get("/{company_id}/research", response_model=list[RunOut])
def list_runs(company_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    company = service.get_by_id(db, company_id)
    return [_run_out(r) for r in reversed(company.runs[-10:])]


@router.patch("/{company_id}/findings/{finding_id}", response_model=AdminCompanyDetail)
def set_finding(company_id: uuid.UUID, finding_id: uuid.UUID, body: FindingStatusIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    f = research.get_finding(db, company_id, finding_id)
    research.set_finding_status(db, f, body.status, user)
    db.commit()
    return mapping.admin_detail(service.get_by_id(db, company_id))
