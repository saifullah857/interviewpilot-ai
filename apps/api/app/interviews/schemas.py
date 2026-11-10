import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

RUBRIC_VERSION = "voice-1"
Kind = Literal["follow_up", "question", "wrap_up"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---- what the AI may return while interviewing ----
class NextTurn(_Strict):
    kind: Kind
    message: str = Field(default="", max_length=600)
    topic: str = Field(default="", max_length=60)
    informed_by: list[int] = Field(default_factory=list, max_length=3)


# ---- what the AI may return when evaluating ----
class CriterionIn(_Strict):
    score: int = Field(ge=0, le=4)
    rationale: str = Field(min_length=10, max_length=400)
    evidence_turns: list[int] = Field(default_factory=list, max_length=4)


class PerAnswerIn(_Strict):
    turn: int
    note: str = Field(min_length=5, max_length=300)
    stronger_answer_hint: str = Field(default="", max_length=300)


class EvalAI(_Strict):
    technical_correctness: CriterionIn
    reasoning: CriterionIn
    clarity: CriterionIn
    specificity: CriterionIn
    strengths: list[str] = Field(min_length=1, max_length=4)
    improvements: list[str] = Field(min_length=1, max_length=4)
    per_answer: list[PerAnswerIn] = Field(default_factory=list, max_length=12)

    @field_validator("strengths", "improvements")
    @classmethod
    def _short(cls, v: list[str]) -> list[str]:
        out = [x.strip() for x in v if x.strip()]
        if not out or any(len(x) > 250 for x in out):
            raise ValueError("Each item must be 1 to 250 characters.")
        return out


# ---- API input ----
class CreateInterviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    resume_id: uuid.UUID
    role: str = Field(min_length=1, max_length=80)
    company: str | None = Field(default=None, max_length=80)
    question_count: int = Field(default=6, ge=4, le=10)
    input_mode: Literal["voice", "text"] = "text"
    consent: bool = False  # must be true: answers are sent to the AI provider and held to run the interview
    save_transcript: bool | None = None  # None = follow the Settings preference


class AnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    text: str = Field(default="", max_length=4000)
    source: Literal["typed", "speech"] = "typed"
    skip: bool = False

    @field_validator("text")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()


class EventIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["mic_denied", "speech_unsupported", "speech_error", "tts_unavailable"]


# ---- API output ----
class EvidenceRef(BaseModel):
    n: int
    url: str
    label: str


class TurnOut(BaseModel):
    id: uuid.UUID
    position: int
    speaker: str
    kind: str
    text: str
    topic: str | None
    source: str
    informed_by: list[EvidenceRef]
    created_at: datetime


class InterviewOut(BaseModel):
    id: uuid.UUID
    status: str
    mode: str
    role: dict
    company: dict | None
    input_mode: str
    question_target: int
    questions_asked: int
    answers_given: int
    awaiting_answer: bool
    label: str = "ai_generated_practice"
    notice: str
    save_transcript: bool
    transcript_available: bool
    transcript_purged_at: datetime | None
    evaluated: bool
    events: list[dict]
    provider: str
    model: str
    started_at: datetime
    last_activity_at: datetime
    ended_at: datetime | None
    server_now: datetime
    idle_minutes: int
    turns: list[TurnOut] | None = None


class InterviewReviewOut(BaseModel):
    interview: InterviewOut
    evaluation: dict | None
