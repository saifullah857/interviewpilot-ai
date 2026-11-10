import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1"
Source = Literal["stated", "inferred"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Skill(_Strict):
    name: str = Field(min_length=1, max_length=60)
    category: Literal["language", "framework", "tool", "concept", "soft", "other"] = "other"
    source: Source
    evidence: str = Field(default="", max_length=200)


class Education(_Strict):
    institution: str = Field(min_length=1, max_length=150)
    degree: str | None = Field(default=None, max_length=150)
    field: str | None = Field(default=None, max_length=150)
    period: str | None = Field(default=None, max_length=60)
    evidence: str = Field(min_length=1, max_length=200)


class Experience(_Strict):
    title: str = Field(min_length=1, max_length=150)
    organization: str | None = Field(default=None, max_length=150)
    period: str | None = Field(default=None, max_length=60)
    summary: str = Field(default="", max_length=400)
    technologies: list[str] = Field(default_factory=list, max_length=15)
    evidence: str = Field(min_length=1, max_length=200)


class Project(_Strict):
    name: str = Field(min_length=1, max_length=150)
    description: str = Field(default="", max_length=400)
    technologies: list[str] = Field(default_factory=list, max_length=15)
    evidence: str = Field(min_length=1, max_length=200)


class Achievement(_Strict):
    text: str = Field(min_length=1, max_length=300)
    measurable: bool = False
    evidence: str = Field(min_length=1, max_length=200)


class Inference(_Strict):
    statement: str = Field(min_length=1, max_length=250)
    basis: str = Field(min_length=1, max_length=250)
    confidence: Literal["low", "medium"] = "low"


class ParsedResume(_Strict):
    education: list[Education] = Field(default_factory=list, max_length=10)
    experience: list[Experience] = Field(default_factory=list, max_length=20)
    projects: list[Project] = Field(default_factory=list, max_length=20)
    skills: list[Skill] = Field(default_factory=list, max_length=80)
    achievements: list[Achievement] = Field(default_factory=list, max_length=20)
    inferences: list[Inference] = Field(default_factory=list, max_length=15)


# ---- API ----
class ValidationReport(BaseModel):
    retries: int = 0
    dropped_ungrounded: int = 0
    downgraded_to_inferred: int = 0
    injection_signals: list[str] = Field(default_factory=list)
    truncated: bool = False


class VersionOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    provider: str
    model: str
    schema_version: str
    parsed: ParsedResume
    report: ValidationReport


class ResumeOut(BaseModel):
    id: uuid.UUID
    filename: str
    kind: str
    size_bytes: int
    pages: int
    created_at: datetime
    analyzed: bool
    duplicate: bool = False
    latest: VersionOut | None = None
    injection_signals: list[str] = Field(default_factory=list)
    truncated: bool = False


class RoleOut(BaseModel):
    slug: str
    title: str
