import re
import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.companies import freshness
from app.companies.schemas import CompanyIn, CompanyPatch, DecisionIn, LocationIn, SourceIn
from app.core.db import utcnow
from app.core.errors import AppError, not_found
from app.models.audit import record
from app.models.company import Company, CompanyLocation, CompanyVerificationRecord, ResearchFinding, ResearchSource
from app.models.user import User

# Which stored labels make sense for which source types.
LABEL_RULES: dict[str, set[str]] = {
    "official_verified": {"official_website", "careers_page", "job_posting", "registry"},
    "public_candidate_report": {"candidate_report"},
    "unverified_or_outdated": {"official_website", "careers_page", "job_posting", "candidate_report", "registry", "other"},
}


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:80] or "company"


def _load(db: Session, stmt):
    return db.scalars(
        stmt.options(
            selectinload(Company.locations),
            selectinload(Company.sources),
            selectinload(Company.verifications),
            selectinload(Company.runs),
            selectinload(Company.findings).selectinload(ResearchFinding.source),
        )
    )


def get_by_id(db: Session, company_id: uuid.UUID) -> Company:
    c = _load(db, select(Company).where(Company.id == company_id)).first()
    if c is None:
        raise not_found("Company")
    return c


def create_company(db: Session, data: CompanyIn, actor: User | None = None) -> Company:
    slug = data.slug or slugify(data.name)
    if db.scalars(select(Company.id).where(Company.slug == slug)).first():
        raise AppError(409, "slug_taken", "A company with this slug already exists.")
    c = Company(
        slug=slug,
        name=data.name.strip(),
        website=str(data.website) if data.website else None,
        careers_url=str(data.careers_url) if data.careers_url else None,
        description=data.description,
        tech_focus=data.tech_focus,
        verification_status="candidate",  # nothing is ever created as verified
    )
    db.add(c)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "slug_taken", "A company with this slug already exists.") from None
    record(db, "company_created", actor.id if actor else None, company_id=str(c.id))
    return c


def update_company(db: Session, c: Company, data: CompanyPatch, actor: User) -> Company:
    sent = data.model_fields_set
    if "website" in sent:
        c.website = str(data.website) if data.website else None
    if "careers_url" in sent:
        c.careers_url = str(data.careers_url) if data.careers_url else None
    if "description" in sent and data.description is not None:
        c.description = data.description
    if "tech_focus" in sent and data.tech_focus is not None:
        c.tech_focus = data.tech_focus
    record(db, "company_updated", actor.id, company_id=str(c.id))
    return c


def add_location(db: Session, c: Company, data: LocationIn, actor: User | None = None) -> CompanyLocation:
    if any(loc.locality.lower() == data.locality.lower() and (loc.address or "") == (data.address or "") and loc.is_lahore == data.is_lahore for loc in c.locations):
        raise AppError(409, "duplicate_location", "This location is already recorded.")
    loc = CompanyLocation(company_id=c.id, locality=data.locality, address=data.address, is_lahore=data.is_lahore)
    c.locations.append(loc)
    db.flush()
    record(db, "location_added", actor.id if actor else None, company_id=str(c.id))
    return loc


def add_source(db: Session, c: Company, data: SourceIn, actor: User | None = None) -> ResearchSource:
    if data.source_type not in {t for ts in LABEL_RULES.values() for t in ts} or data.source_type not in LABEL_RULES[data.label]:
        raise AppError(422, "label_mismatch", f"Label '{data.label}' is not allowed for source type '{data.source_type}'.")
    if data.retrieved_at.tzinfo is None:
        raise AppError(422, "naive_datetime", "retrieved_at must include a timezone.")
    if data.retrieved_at > utcnow() + timedelta(days=1):
        raise AppError(422, "future_date", "retrieved_at cannot be in the future.")
    url = str(data.url)
    if any(s.url == url for s in c.sources):
        raise AppError(409, "duplicate_source", "This URL is already recorded for the company.")
    s = ResearchSource(
        company_id=c.id,
        url=url,
        source_type=data.source_type,
        label=data.label,
        supports_lahore=data.supports_lahore,
        excerpt=data.excerpt,
        retrieved_at=data.retrieved_at,
        status="unreviewed",
        added_by=actor.id if actor else None,
    )
    c.sources.append(s)
    db.flush()
    record(db, "source_added", actor.id if actor else None, company_id=str(c.id), source_id=str(s.id))
    return s


def set_source_status(db: Session, s: ResearchSource, status: str, actor: User) -> None:
    s.status = status
    if status == "rejected":  # findings that rest on a rejected source can't stay approved
        for f in s.company.findings:
            if f.source_id == s.id and f.status != "rejected":
                f.status = "rejected"
    record(db, "source_status_changed", actor.id, source_id=str(s.id), status=status)


def decide(db: Session, c: Company, reviewer: User | None, data: DecisionIn) -> CompanyVerificationRecord:
    """Apply a human review decision. Verification needs a Lahore location, official evidence that supports it, and notes."""
    now = utcnow()
    notes = data.notes.strip()
    chosen = {str(i) for i in data.evidence_ids}
    by_id = {str(s.id): s for s in c.sources}
    if not chosen <= set(by_id):
        raise AppError(422, "unknown_evidence", "Some evidence IDs do not belong to this company.")

    if data.decision == "verified":
        unmet = []
        if not any(loc.is_lahore for loc in c.locations):
            unmet.append("Add at least one location marked as Lahore.")
        supporting = [by_id[i] for i in chosen if by_id[i].label == "official_verified" and by_id[i].supports_lahore]
        if not supporting:
            unmet.append("Select at least one official_verified source that supports the Lahore presence.")
        if len(notes) < 10:
            unmet.append("Write review notes (at least 10 characters).")
        if unmet:
            raise AppError(422, "verification_requirements_not_met", "This company cannot be verified yet.", unmet)
        for i in chosen:
            by_id[i].status = "active"
        for loc in c.locations:
            if loc.is_lahore:
                loc.verified_at = now
        c.verification_status, c.last_verified_at = "verified_lahore", now
    elif data.decision == "rejected":
        if len(notes) < 10:
            raise AppError(422, "notes_required", "Explain the rejection (at least 10 characters).")
        c.verification_status = "rejected"
    else:  # marked_stale
        if c.verification_status != "verified_lahore":
            raise AppError(409, "not_verified", "Only a verified company can be marked stale.")
        c.verification_status = "stale"

    rec = CompanyVerificationRecord(company_id=c.id, reviewer_id=reviewer.id if reviewer else None, decision=data.decision, notes=notes, evidence_ids=sorted(chosen))
    c.verifications.append(rec)
    db.flush()
    record(db, "verification_decision", reviewer.id if reviewer else None, company_id=str(c.id), decision=data.decision)
    return rec


def lahore_localities(c: Company) -> list[str]:
    return sorted({loc.locality for loc in c.locations if loc.is_lahore})


def list_verified(db: Session, q: str | None, locality: str | None, tech: str | None, page: int, page_size: int):
    """Only verified_lahore companies with a Lahore location are ever returned. The directory is small, so filtering
    and paging happen in Python, which keeps the behaviour identical on SQLite and PostgreSQL."""
    rows = _load(db, select(Company).where(Company.verification_status == "verified_lahore").order_by(Company.name)).all()
    rows = [c for c in rows if lahore_localities(c)]
    if locality:
        rows = [c for c in rows if locality.lower() in (x.lower() for x in lahore_localities(c))]
    if tech:
        rows = [c for c in rows if tech.lower() in (t.lower() for t in c.tech_focus)]
    if q:
        needle = q.lower()
        rows = [c for c in rows if needle in c.name.lower() or any(needle in t.lower() for t in c.tech_focus)]
    total = len(rows)
    start = (page - 1) * page_size
    return rows[start : start + page_size], total


def get_verified_by_slug(db: Session, slug: str) -> Company:
    c = _load(db, select(Company).where(Company.slug == slug, Company.verification_status == "verified_lahore")).first()
    if c is None or not lahore_localities(c):
        raise not_found("Company")  # candidates, rejected and stale companies are indistinguishable from missing ones
    return c


def get_selectable_by_slug(db: Session, slug: str) -> Company:
    """A company a signed-in user may choose for practice: verified, stale or still a candidate, never a rejected one.
    Only verified companies get company-informed content; the rest fall back to general preparation with a notice."""
    c = _load(db, select(Company).where(Company.slug == slug, Company.verification_status != "rejected")).first()
    if c is None:
        raise not_found("Company")
    return c


def verified_localities(db: Session) -> list[str]:
    rows = _load(db, select(Company).where(Company.verification_status == "verified_lahore")).all()
    return sorted({loc for c in rows for loc in lahore_localities(c)})


def mark_overdue_stale(db: Session) -> int:
    now, n = utcnow(), 0
    for c in _load(db, select(Company).where(Company.verification_status == "verified_lahore")).all():
        if freshness.needs_recheck(c.last_verified_at, now):
            c.verification_status = "stale"
            c.verifications.append(
                CompanyVerificationRecord(
                    company_id=c.id, reviewer_id=None, decision="marked_stale", notes="Automatic: office evidence is past the 180-day freshness limit.", evidence_ids=[]
                )
            )
            n += 1
    db.flush()
    return n
