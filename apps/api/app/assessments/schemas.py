import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

SCHEMA_VERSION = "1"
Difficulty = Literal["easy", "medium", "hard"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---- what the AI may return ----
class GenQuestion(_Strict):
    type: Literal["mcq", "short_answer"]
    prompt: str = Field(min_length=20, max_length=600)
    options: list[str] = Field(default_factory=list, max_length=6)
    correct_index: int | None = Field(default=None, ge=0, le=5)
    reference_points: list[str] = Field(default_factory=list, max_length=6)
    explanation: str = Field(min_length=10, max_length=500)
    topic: str = Field(min_length=2, max_length=60)
    skills: list[str] = Field(min_length=1, max_length=5)
    difficulty: Difficulty
    informed_by: list[int] = Field(default_factory=list, max_length=5)

    @field_validator("skills")
    @classmethod
    def _skills(cls, v: list[str]) -> list[str]:
        out = [s.strip() for s in v if s.strip()]
        if not out or any(len(s) > 40 for s in out):
            raise ValueError("Skills must be 1 to 40 characters each.")
        return out

    @field_validator("options", "reference_points")
    @classmethod
    def _strip(cls, v: list[str]) -> list[str]:
        if any(len(x) > 300 for x in v):
            raise ValueError("Each option or point must be at most 300 characters.")
        return [x.strip() for x in v]


class GenBatch(_Strict):
    questions: list[GenQuestion] = Field(default_factory=list, max_length=12)


class VerifyItem(_Strict):
    id: int
    choice: int | None = Field(default=None, ge=0, le=5)
    ambiguous: bool = False
    clear: bool = True


class VerifyBatch(_Strict):
    answers: list[VerifyItem] = Field(default_factory=list, max_length=30)


# ---- API ----
class CreateAssessmentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resume_id: uuid.UUID
    role: str = Field(min_length=1, max_length=80)
    company: str | None = Field(default=None, max_length=80)
    question_count: int = Field(default=20, ge=10, le=30)
    duration_minutes: int | None = Field(default=None, ge=10, le=120)


class AnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question_id: uuid.UUID
    selected_index: int | None = Field(default=None, ge=0, le=5)
    response_text: str | None = Field(default=None, max_length=4000)


class AnswersIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answers: list[AnswerIn] = Field(min_length=1, max_length=40)


class EvidenceRef(BaseModel):
    url: str
    label: str


class OptionOut(BaseModel):
    index: int
    text: str


class QuestionOut(BaseModel):
    """What the browser gets while the test is running: no answer key, no explanation."""

    id: uuid.UUID
    position: int
    type: str
    category: str
    prompt: str
    options: list[OptionOut]
    difficulty: str
    topic: str
    label: str
    informed_by: list[EvidenceRef]
    max_points: int


class SavedAnswer(BaseModel):
    question_id: uuid.UUID
    selected_index: int | None
    response_text: str | None


class AssessmentOut(BaseModel):
    id: uuid.UUID
    status: str
    mode: str
    role: dict
    company: dict | None
    notice: str | None
    question_count: int
    duration_minutes: int
    created_at: datetime
    started_at: datetime | None
    deadline_at: datetime | None
    submitted_at: datetime | None
    auto_submitted: bool
    server_now: datetime
    error_code: str | None
    message: str | None
    generation: dict
    score: dict | None = None
    questions: list[QuestionOut] | None = None
    answers: list[SavedAnswer] | None = None


class ReviewQuestion(QuestionOut):
    correct_index: int | None
    reference_points: list[str]
    explanation: str
    selected_index: int | None
    response_text: str | None
    is_correct: bool | None
    needs_evaluation: bool


class ReviewOut(BaseModel):
    assessment: AssessmentOut
    questions: list[ReviewQuestion]
    result: dict
