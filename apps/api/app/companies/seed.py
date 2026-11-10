"""Seed import. Imports candidates only; it can never create or change a verification status."""

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.companies import service
from app.companies.schemas import CompanyIn, LocationIn, SourceIn
from app.models.company import Company

DEFAULT_SEED = Path(__file__).resolve().parents[4] / "data" / "company_seed" / "lahore_candidates.json"


class SeedCompany(CompanyIn):
    # CompanyIn already forbids unknown fields, so a seed file containing 'verification_status' is rejected.
    locations: list[LocationIn] = Field(default_factory=list)
    sources: list[SourceIn] = Field(default_factory=list)


class SeedFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    meta: dict = Field(alias="_meta")
    companies: list[SeedCompany]


def load_seed(path: Path) -> SeedFile:
    return SeedFile.model_validate(json.loads(path.read_text(encoding="utf-8")))


def import_seed(db: Session, path: Path = DEFAULT_SEED) -> dict[str, int]:
    seed = load_seed(path)
    out = {"created": 0, "updated": 0, "locations_added": 0, "sources_added": 0}
    for item in seed.companies:
        slug = item.slug or service.slugify(item.name)
        existing = db.scalars(select(Company).where(Company.slug == slug)).first()
        if existing is None:
            c = service.create_company(db, CompanyIn(**item.model_dump(include=set(CompanyIn.model_fields))), None)
            out["created"] += 1
        else:
            c = service.get_by_id(db, existing.id)
            c.name, c.description, c.tech_focus = item.name, item.description or c.description, item.tech_focus or c.tech_focus
            c.website = str(item.website) if item.website else c.website
            c.careers_url = str(item.careers_url) if item.careers_url else c.careers_url
            out["updated"] += 1
        for loc in item.locations:
            known = {(x.locality.lower(), x.address or "", x.is_lahore) for x in c.locations}
            if (loc.locality.lower(), loc.address or "", loc.is_lahore) in known:
                continue
            service.add_location(db, c, loc)
            out["locations_added"] += 1
        for src in item.sources:
            if any(s.url == str(src.url) for s in c.sources):
                continue
            service.add_source(db, c, src)
            out["sources_added"] += 1
    db.commit()
    return out
