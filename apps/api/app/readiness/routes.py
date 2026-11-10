import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.core.db import get_db
from app.models.user import User
from app.readiness import service

router = APIRouter(prefix="/readiness", tags=["readiness"])


@router.get("")
def readiness(role: str = Query(max_length=80), company: str | None = Query(default=None, max_length=80), resume_id: uuid.UUID | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.report(db, user, role, company, resume_id)


@router.get("/roles")
def roles_list(company: str | None = Query(default=None, max_length=80), resume_id: uuid.UUID | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.role_matches(db, user, company, resume_id)


@router.get("/companies")
def companies_list(role: str = Query(max_length=80), resume_id: uuid.UUID | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.company_matches(db, user, role, resume_id)
