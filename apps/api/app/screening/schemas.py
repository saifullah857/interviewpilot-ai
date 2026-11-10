import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.questions.schemas import QuestionOut

Level = Literal["easy", "medium", "hard", "mixed"]


class CreateScreeningIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: str = Field(min_length=1, max_length=80)
    company: str | None = Field(default=None, max_length=80)
    level: Level = "mixed"
    count: int = Field(default=20, ge=5, le=40)


class AnswerIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=80)
    choice: int | None = Field(default=None, ge=0, le=5)  # None clears the answer


class ScreeningOut(BaseModel):
    id: uuid.UUID
    status: str
    company: dict | None
    role: str
    level: str
    started_at: datetime
    deadline_at: datetime
    server_now: datetime
    total: int
    answered: int
    questions: list[QuestionOut]
    answers: dict[str, int]


class ScreeningSummary(BaseModel):
    id: uuid.UUID
    status: str
    company: dict | None
    role: str
    level: str
    submitted_at: datetime | None
    correct: int | None
    total: int
    score: int | None


class ReviewItem(BaseModel):
    slug: str
    category: str
    difficulty: str
    kind: str
    prompt: str
    options: list[str]
    chosen: int | None
    answer_index: int
    correct: bool
    explanation: str


class ScreeningResult(BaseModel):
    session: ScreeningSummary
    auto_submitted: bool
    by_category: list[dict]
    by_difficulty: list[dict]
    next_step: dict
    review: list[ReviewItem]
    note: str
