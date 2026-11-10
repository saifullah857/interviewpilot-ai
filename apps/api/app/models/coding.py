import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, UTCDateTime, utcnow


class CodingProblem(Base):
    """A practice problem. hidden_tests and reference_solution never leave the server before a session is finished."""

    __tablename__ = "coding_problems"
    __table_args__ = (
        CheckConstraint("label in ('ai_generated_practice')", name="label_valid"),
        CheckConstraint("difficulty in ('easy','medium','hard')", name="difficulty_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    difficulty: Mapped[str] = mapped_column(String(8))
    minutes: Mapped[int] = mapped_column(Integer)
    topics: Mapped[list] = mapped_column(JSON, default=list)
    roles: Mapped[list] = mapped_column(JSON, default=list)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    ds: Mapped[list] = mapped_column(JSON, default=list)
    statement: Mapped[str] = mapped_column(Text)
    constraints: Mapped[list] = mapped_column(JSON, default=list)
    entry_point: Mapped[str] = mapped_column(String(64))
    signature: Mapped[str] = mapped_column(String(200))
    starter_code: Mapped[str] = mapped_column(Text)
    examples: Mapped[list] = mapped_column(JSON, default=list)
    visible_tests: Mapped[list] = mapped_column(JSON, default=list)
    hidden_tests: Mapped[list] = mapped_column(JSON, default=list)
    per_test_ms: Mapped[int] = mapped_column(Integer, default=2000)
    complexity: Mapped[dict] = mapped_column(JSON, default=dict)
    approach: Mapped[str] = mapped_column(Text, default="")
    reference_solution: Mapped[str] = mapped_column(Text, default="")
    label: Mapped[str] = mapped_column(String(24), default="ai_generated_practice")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)


class CodingSession(Base):
    __tablename__ = "coding_sessions"
    __table_args__ = (CheckConstraint("status in ('in_progress','submitted')", name="status_valid"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("assessments.id", ondelete="SET NULL"), nullable=True)
    problem_slugs: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(12), default="in_progress")
    drafts: Mapped[dict] = mapped_column(JSON, default=dict)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    deadline_at: Mapped[datetime] = mapped_column(UTCDateTime)
    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    auto_submitted: Mapped[bool] = mapped_column(Boolean, default=False)
    company_slug: Mapped[str | None] = mapped_column(String(80), nullable=True)  # software house whose focus shaped the problem choice
    resume_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)  # resume whose skills shaped the problem choice
    language: Mapped[str] = mapped_column(String(12), default="python")
    plan: Mapped[dict] = mapped_column(JSON, default=dict)  # why these problems were chosen (shown to the user)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    submissions: Mapped[list["CodingSubmission"]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by="CodingSubmission.created_at")


class CodingSubmission(Base):
    __tablename__ = "coding_submissions"
    __table_args__ = (
        CheckConstraint("kind in ('run','submit')", name="kind_valid"),
        CheckConstraint("status in ('completed','not_executed')", name="status_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("coding_sessions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    problem_slug: Mapped[str] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(6))
    language: Mapped[str] = mapped_column(String(12), default="python")
    code: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(12))
    compile_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    results: Mapped[list] = mapped_column(JSON, default=list)  # already redacted: hidden-test details are never stored here
    passed_count: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None when nothing was executed
    total_count: Mapped[int] = mapped_column(Integer)
    runtime_ms: Mapped[float | None] = mapped_column(Float, nullable=True)
    runner_backend: Mapped[str] = mapped_column(String(40))
    runner_version: Mapped[str] = mapped_column(String(40), default="")
    executed: Mapped[bool] = mapped_column(Boolean, default=False)
    feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # subjective AI commentary, kept apart from test results
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    session: Mapped[CodingSession] = relationship(back_populates="submissions")
