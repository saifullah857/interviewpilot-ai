import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, field_validator

SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SourceType = Literal["official_website", "careers_page", "job_posting", "candidate_report", "registry", "other"]
Label = Literal["official_verified", "public_candidate_report", "unverified_or_outdated"]


def _clean_url(v: AnyHttpUrl | str | None) -> str | None:
    return None if v is None else str(v)


class LocationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    locality: str = Field(min_length=2, max_length=80)
    address: str | None = Field(default=None, max_length=300)
    is_lahore: bool = True

    @field_validator("locality")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class SourceIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: AnyHttpUrl
    source_type: SourceType
    label: Label
    supports_lahore: bool = False
    excerpt: str = Field(default="", max_length=500)
    retrieved_at: datetime


class CompanyIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=2, max_length=200)
    slug: str | None = Field(default=None, max_length=80)
    website: AnyHttpUrl | None = None
    careers_url: AnyHttpUrl | None = None
    description: str = Field(default="", max_length=2000)
    tech_focus: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("slug")
    @classmethod
    def _slug(cls, v: str | None) -> str | None:
        if v is not None and not SLUG_RE.match(v):
            raise ValueError("Slug must be lower-case letters, digits and hyphens.")
        return v

    @field_validator("tech_focus")
    @classmethod
    def _tech(cls, v: list[str]) -> list[str]:
        out = [t.strip() for t in v if t.strip()]
        if any(len(t) > 40 for t in out):
            raise ValueError("Each technology must be at most 40 characters.")
        return out


class CompanyPatch(BaseModel):
    """Descriptive fields only. Status can only change through a verification decision."""

    model_config = ConfigDict(extra="forbid")
    website: AnyHttpUrl | None = None
    careers_url: AnyHttpUrl | None = None
    description: str | None = Field(default=None, max_length=2000)
    tech_focus: list[str] | None = Field(default=None, max_length=20)

    @field_validator("tech_focus")
    @classmethod
    def _tech(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        out = [t.strip() for t in v if t.strip()]
        if any(len(t) > 40 for t in out):
            raise ValueError("Each technology must be at most 40 characters.")
        return out


class DecisionIn(BaseModel):
    decision: Literal["verified", "rejected", "marked_stale"]
    evidence_ids: list[uuid.UUID] = Field(default_factory=list, max_length=50)
    notes: str = Field(default="", max_length=2000)


class SourceStatusIn(BaseModel):
    status: Literal["unreviewed", "active", "rejected"]


# ---- outputs ----
class LocationOut(BaseModel):
    id: uuid.UUID
    locality: str
    address: str | None
    is_lahore: bool
    verified_at: datetime | None


class PublicSourceOut(BaseModel):
    id: uuid.UUID
    url: str
    source_type: str
    label: str  # effective label: becomes unverified_or_outdated when evidence is past its freshness limit
    stored_label: str
    retrieved_at: datetime
    excerpt: str


class AdminSourceOut(PublicSourceOut):
    supports_lahore: bool
    status: str


class VerificationOut(BaseModel):
    id: uuid.UUID
    decision: str
    notes: str
    evidence_ids: list[str]
    reviewer_id: uuid.UUID | None
    created_at: datetime


class CompanyListItem(BaseModel):
    slug: str
    name: str
    description: str
    tech_focus: list[str]
    localities: list[str]
    website: str | None
    careers_url: str | None
    last_verified_at: datetime | None
    needs_recheck: bool
    evidence_count: int


class RequirementOut(BaseModel):
    id: uuid.UUID
    kind: str
    role_title: str | None
    text: str
    skills: list[str]
    years_experience: int | None
    scope: str
    label: str
    source_url: str
    retrieved_at: datetime


class CompanyListOut(BaseModel):
    items: list[CompanyListItem]
    total: int
    page: int
    page_size: int


class CompanyDetailOut(CompanyListItem):
    locations: list[LocationOut]
    sources: list[PublicSourceOut]
    requirements: list[RequirementOut] = []


class AdminCompanyListItem(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    verification_status: str
    locations: int
    sources: int
    last_verified_at: datetime | None


class AdminCompanyDetail(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    website: str | None
    careers_url: str | None
    description: str
    tech_focus: list[str]
    verification_status: str
    last_verified_at: datetime | None
    locations: list[LocationOut]
    sources: list[AdminSourceOut]
    verifications: list[VerificationOut]
    findings: list[dict] = []
    latest_run: dict | None = None
