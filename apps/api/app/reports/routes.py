import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.core.db import get_db
from app.models.audit import record
from app.models.report import Report
from app.models.user import User
from app.reports import dashboard, service
from app.reports.schemas import CreateReportIn, ReportOut, ReportSummary, RoadmapIn

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=ReportOut, status_code=201)
def create_report(body: CreateReportIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.out(db, service.create(db, user, body))


@router.get("", response_model=list[ReportSummary])
def list_reports(role: str | None = Query(default=None, max_length=80), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(Report).where(Report.user_id == user.id).order_by(Report.created_at.desc())
    if role:
        q = q.where(Report.role_slug == role)
    return [service.summary(db, r) for r in db.scalars(q).all()]


@router.get("/sources")
def report_sources(role: str = Query(max_length=80), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.sources(db, user, role)


@router.get("/dashboard")
def report_dashboard(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return dashboard.build(db, user)


@router.get("/progress")
def report_progress(role: str | None = Query(default=None, max_length=80), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.progress(db, user, role)


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.out(db, service.get_owned(db, report_id, user))


@router.post("/{report_id}/roadmap", response_model=ReportOut)
def new_roadmap(report_id: uuid.UUID, body: RoadmapIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.out(db, service.regenerate_roadmap(db, user, service.get_owned(db, report_id, user), body.horizon))


@router.delete("/{report_id}", status_code=204)
def delete_report(report_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    r = service.get_owned(db, report_id, user)
    db.delete(r)
    record(db, "report_deleted", user.id, report_id=str(report_id))
    db.commit()
    return Response(status_code=204)
