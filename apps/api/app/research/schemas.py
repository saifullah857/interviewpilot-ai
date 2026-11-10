import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Kind = Literal["role_requirement", "tech_stack", "interview_format", "responsibility"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FindingIn(_Strict):
    """What the AI may return for one page. There is deliberately no URL field: sources come only from our own search step."""

    kind: Kind
    role_title: str | None = Field(default=None, max_length=100)
    text: str = Field(min_length=8, max_length=300)
    skills: list[str] = Field(default_factory=list, max_length=12)
    years_experience: int | None = Field(default=None, ge=0, le=30)
    quote: str = Field(min_length=8, max_length=200)

    @field_validator("skills")
    @classmethod
    def _skills(cls, v: list[str]) -> list[str]:
        out = [s.strip() for s in v if s.strip()]
        if any(len(s) > 40 for s in out):
            raise ValueError("Each skill must be at most 40 characters.")
        return out


class Extraction(_Strict):
    findings: list[FindingIn] = Field(default_factory=list, max_length=15)


# ---- API ----
class RunOut(BaseModel):
    id: uuid.UUID
    status: str
    error_code: str | None
    summary: dict
    started_at: datetime
    finished_at: datetime | None
    cached: bool = False


class FindingOut(BaseModel):
    id: uuid.UUID
    kind: str
    role_title: str | None
    text: str
    skills: list[str]
    years_experience: int | None
    scope: str
    label: str  # effective evidence label of its source (freshness applied)
    source_url: str
    source_type: str
    retrieved_at: datetime


class AdminFindingOut(FindingOut):
    status: str
    source_id: uuid.UUID
    source_status: str


class FindingStatusIn(BaseModel):
    status: Literal["unreviewed", "active", "rejected"]
