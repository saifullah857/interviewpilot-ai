import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_admin
from app.companies import mapping, service
from app.companies.schemas import (
    AdminCompanyDetail,
    AdminCompanyListItem,
    CompanyDetailOut,
    CompanyIn,
    CompanyListOut,
    CompanyPatch,
    DecisionIn,
    LocationIn,
    SourceIn,
    SourceStatusIn,
)
from app.core.db import get_db
from app.core.errors import not_found
from app.models.company import Company, ResearchSource
from app.models.user import User

router = APIRouter(prefix="/companies", tags=["companies"], dependencies=[Depends(get_current_user)])
admin = APIRouter(prefix="/admin/companies", tags=["admin"])


@router.get("", response_model=CompanyListOut)
def list_companies(
    q: str | None = Query(default=None, max_length=100),
    locality: str | None = Query(default=None, max_length=80),
    tech: str | None = Query(default=None, max_length=40),
    page: int = Query(default=1, ge=1, le=1000),
    page_size: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    rows, total = service.list_verified(db, q, locality, tech, page, page_size)
    return CompanyListOut(items=[mapping.list_item(c) for c in rows], total=total, page=page, page_size=page_size)


@router.get("/localities", response_model=list[str])
def localities(db: Session = Depends(get_db)):
    return service.verified_localities(db)


@router.get("/{slug}", response_model=CompanyDetailOut)
def company_detail(slug: str, db: Session = Depends(get_db)):
    return mapping.detail(service.get_verified_by_slug(db, slug))


# ---------------- admin ----------------
@admin.get("", response_model=list[AdminCompanyListItem])
def admin_list(status: str | None = Query(default=None, max_length=20), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    stmt = select(Company).order_by(Company.name)
    if status:
        stmt = stmt.where(Company.verification_status == status)
    rows = service._load(db, stmt).all()
    return [mapping.admin_item(c) for c in rows]


@admin.post("", response_model=AdminCompanyDetail, status_code=201)
def admin_create(body: CompanyIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    c = service.create_company(db, body, user)
    db.commit()
    return mapping.admin_detail(service.get_by_id(db, c.id))


@admin.get("/{company_id}", response_model=AdminCompanyDetail)
def admin_get(company_id: uuid.UUID, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    return mapping.admin_detail(service.get_by_id(db, company_id))


@admin.patch("/{company_id}", response_model=AdminCompanyDetail)
def admin_update(company_id: uuid.UUID, body: CompanyPatch, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    c = service.get_by_id(db, company_id)
    service.update_company(db, c, body, user)
    db.commit()
    return mapping.admin_detail(service.get_by_id(db, company_id))


@admin.post("/{company_id}/locations", response_model=AdminCompanyDetail, status_code=201)
def admin_add_location(company_id: uuid.UUID, body: LocationIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    c = service.get_by_id(db, company_id)
    service.add_location(db, c, body, user)
    db.commit()
    return mapping.admin_detail(service.get_by_id(db, company_id))


@admin.post("/{company_id}/sources", response_model=AdminCompanyDetail, status_code=201)
def admin_add_source(company_id: uuid.UUID, body: SourceIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    c = service.get_by_id(db, company_id)
    service.add_source(db, c, body, user)
    db.commit()
    return mapping.admin_detail(service.get_by_id(db, company_id))


@admin.patch("/{company_id}/sources/{source_id}", response_model=AdminCompanyDetail)
def admin_source_status(company_id: uuid.UUID, source_id: uuid.UUID, body: SourceStatusIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    s = db.scalars(select(ResearchSource).where(ResearchSource.id == source_id, ResearchSource.company_id == company_id)).first()
    if s is None:
        raise not_found("Source")
    service.set_source_status(db, s, body.status, user)
    db.commit()
    return mapping.admin_detail(service.get_by_id(db, company_id))


@admin.post("/{company_id}/verification", response_model=AdminCompanyDetail)
def admin_decide(company_id: uuid.UUID, body: DecisionIn, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    c = service.get_by_id(db, company_id)
    service.decide(db, c, user, body)
    db.commit()
    return mapping.admin_detail(service.get_by_id(db, company_id))
