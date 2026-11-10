from app.companies import freshness
from app.companies.schemas import (
    AdminCompanyDetail,
    AdminCompanyListItem,
    AdminSourceOut,
    CompanyDetailOut,
    CompanyListItem,
    LocationOut,
    PublicSourceOut,
    RequirementOut,
    VerificationOut,
)
from app.companies.service import lahore_localities
from app.core.db import utcnow
from app.models.company import Company, CompanyLocation, ResearchSource


def _loc(loc: CompanyLocation) -> LocationOut:
    return LocationOut(id=loc.id, locality=loc.locality, address=loc.address, is_lahore=loc.is_lahore, verified_at=loc.verified_at)


def _public_source(s: ResearchSource) -> PublicSourceOut:
    return PublicSourceOut(
        id=s.id,
        url=s.url,
        source_type=s.source_type,
        label=freshness.effective_label(s.label, s.source_type, s.retrieved_at, utcnow()),
        stored_label=s.label,
        retrieved_at=s.retrieved_at,
        excerpt=s.excerpt,
    )


def _active(c: Company) -> list[ResearchSource]:
    return [s for s in c.sources if s.status == "active"]


def list_item(c: Company) -> CompanyListItem:
    return CompanyListItem(
        slug=c.slug,
        name=c.name,
        description=c.description,
        tech_focus=list(c.tech_focus or []),
        localities=lahore_localities(c),
        website=c.website,
        careers_url=c.careers_url,
        last_verified_at=c.last_verified_at,
        needs_recheck=freshness.needs_recheck(c.last_verified_at, utcnow()),
        evidence_count=len(_active(c)),
    )


def _requirements(c: Company) -> list[RequirementOut]:
    from app.research.service import active_findings, effective_label

    return [
        RequirementOut(
            id=f.id,
            kind=f.kind,
            role_title=f.role_title,
            text=f.text,
            skills=list(f.skills or []),
            years_experience=f.years_experience,
            scope=f.scope,
            label=effective_label(f),
            source_url=f.source.url,
            retrieved_at=f.retrieved_at,
        )
        for f in active_findings(c)
    ]


def _admin_findings(c: Company) -> list[dict]:
    from app.research.service import effective_label

    return [
        {
            "id": str(f.id),
            "kind": f.kind,
            "role_title": f.role_title,
            "text": f.text,
            "skills": list(f.skills or []),
            "years_experience": f.years_experience,
            "scope": f.scope,
            "label": effective_label(f),
            "source_url": f.source.url,
            "source_type": f.source.source_type,
            "retrieved_at": f.retrieved_at.isoformat(),
            "status": f.status,
            "source_id": str(f.source_id),
            "source_status": f.source.status,
        }
        for f in c.findings
    ]


def _run(r) -> dict:
    return {
        "id": str(r.id),
        "status": r.status,
        "error_code": r.error_code,
        "summary": r.summary or {},
        "started_at": r.started_at.isoformat(),
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
    }


def detail(c: Company) -> CompanyDetailOut:
    # Public detail never exposes non-Lahore locations or unreviewed/rejected evidence.
    return CompanyDetailOut(
        **list_item(c).model_dump(),
        locations=[_loc(x) for x in c.locations if x.is_lahore],
        sources=[_public_source(s) for s in _active(c)],
        requirements=_requirements(c),
    )


def admin_item(c: Company) -> AdminCompanyListItem:
    return AdminCompanyListItem(
        id=c.id,
        slug=c.slug,
        name=c.name,
        verification_status=c.verification_status,
        locations=len(c.locations),
        sources=len(c.sources),
        last_verified_at=c.last_verified_at,
    )


def admin_detail(c: Company) -> AdminCompanyDetail:
    return AdminCompanyDetail(
        id=c.id,
        slug=c.slug,
        name=c.name,
        website=c.website,
        careers_url=c.careers_url,
        description=c.description,
        tech_focus=list(c.tech_focus or []),
        verification_status=c.verification_status,
        last_verified_at=c.last_verified_at,
        locations=[_loc(x) for x in c.locations],
        sources=[AdminSourceOut(**_public_source(s).model_dump(), supports_lahore=s.supports_lahore, status=s.status) for s in c.sources],
        findings=_admin_findings(c),
        latest_run=_run(c.runs[-1]) if c.runs else None,
        verifications=[
            VerificationOut(id=v.id, decision=v.decision, notes=v.notes, evidence_ids=list(v.evidence_ids or []), reviewer_id=v.reviewer_id, created_at=v.created_at)
            for v in c.verifications
        ],
    )
