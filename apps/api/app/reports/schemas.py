import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class CreateReportIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str = Field(min_length=1, max_length=80)
    resume_id: uuid.UUID | None = None
    assessment_id: uuid.UUID | None = None
    coding_session_id: uuid.UUID | None = None
    interview_id: uuid.UUID | None = None
    horizon: Literal[7, 30] = 7


class RoadmapIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    horizon: Literal[7, 30]


class ReportSummary(BaseModel):
    id: uuid.UUID
    created_at: datetime
    role: dict
    company: dict | None
    mode: str
    horizon: int
    overall: int | None
    scores: dict
    included: list[str]
    missing: list[str]
    auto: bool = False


class ReportOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    role: dict
    company: dict | None
    mode: str
    horizon: int
    rubric_version: str
    rubric: dict
    sources_used: dict
    components: list[dict]
    overall: dict
    gaps: list[dict]
    strengths: list[dict]
    practice_questions: list[dict]
    sources: list[dict]
    roadmap: dict
    notes: list[str]
    previous: dict | None
    disclaimer: str
    provider: str
    model: str
    auto: bool = False
