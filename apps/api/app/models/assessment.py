import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, UTCDateTime, utcnow

STATUSES = ("generating", "ready", "in_progress", "submitted", "failed")
QTYPES = ("mcq", "short_answer")
CATEGORIES = ("technical", "role_problem_solving", "resume_project", "company_informed")


def _in(col: str, values: tuple[str, ...]) -> str:
    return f"{col} in ({', '.join(repr(v) for v in values)})"


class Assessment(Base):
    __tablename__ = "assessments"
    __table_args__ = (
        CheckConstraint(_in("status", STATUSES), name="status_valid"),
        CheckConstraint("mode in ('general','company')", name="mode_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    resume_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True)
    role_slug: Mapped[str] = mapped_column(String(80))
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    mode: Mapped[str] = mapped_column(String(10), default="general")
    status: Mapped[str] = mapped_column(String(12), default="generating")
    question_target: Mapped[int] = mapped_column(Integer)
    question_count: Mapped[int] = mapped_column(Integer, default=0)
    duration_minutes: Mapped[int] = mapped_column(Integer)
    notice: Mapped[str | None] = mapped_column(String(300), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    schema_version: Mapped[str] = mapped_column(String(8), default="1")
    provider: Mapped[str | None] = mapped_column(String(30), nullable=True)
    model: Mapped[str | None] = mapped_column(String(100), nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    deadline_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    auto_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    questions: Mapped[list["AssessmentQuestion"]] = relationship(back_populates="assessment", cascade="all, delete-orphan", order_by="AssessmentQuestion.position")
    answers: Mapped[list["AssessmentAnswer"]] = relationship(back_populates="assessment", cascade="all, delete-orphan")


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"
    __table_args__ = (
        UniqueConstraint("assessment_id", "position", name="uq_assessment_questions_position"),
        CheckConstraint(_in("type", QTYPES), name="type_valid"),
        CheckConstraint(_in("category", CATEGORIES), name="category_valid"),
        CheckConstraint("label in ('ai_generated_practice')", name="label_valid"),  # generated questions are never anything else
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    type: Mapped[str] = mapped_column(String(14))
    category: Mapped[str] = mapped_column(String(24))
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list)
    correct_index: Mapped[int | None] = mapped_column(Integer, nullable=True)  # never sent to the browser before submission
    reference_points: Mapped[list] = mapped_column(JSON, default=list)  # same for short-answer model points
    explanation: Mapped[str] = mapped_column(Text, default="")
    topic: Mapped[str] = mapped_column(String(60))
    skills: Mapped[list] = mapped_column(JSON, default=list)
    difficulty: Mapped[str] = mapped_column(String(8))
    informed_by: Mapped[list] = mapped_column(JSON, default=list)  # snapshot of approved evidence that inspired a company question
    label: Mapped[str] = mapped_column(String(24), default="ai_generated_practice")

    assessment: Mapped[Assessment] = relationship(back_populates="questions")


class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"
    __table_args__ = (UniqueConstraint("question_id", name="uq_assessment_answers_question"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessments.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_questions.id", ondelete="CASCADE"))
    selected_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_correct: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    assessment: Mapped[Assessment] = relationship(back_populates="answers")
