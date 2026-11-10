import uuid
from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, UTCDateTime, utcnow


class ScreeningSession(Base):
    """One timed online screening test (MCQ and output questions). Scored by rules only, never by AI."""

    __tablename__ = "screening_sessions"
    __table_args__ = (CheckConstraint("status in ('in_progress','submitted')", name="status_valid"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company_slug: Mapped[str | None] = mapped_column(String(80), nullable=True)
    role_slug: Mapped[str] = mapped_column(String(80))
    level: Mapped[str] = mapped_column(String(8), default="mixed")
    question_slugs: Mapped[list] = mapped_column(JSON, default=list)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)  # question slug -> chosen option index
    status: Mapped[str] = mapped_column(String(12), default="in_progress", index=True)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    deadline_at: Mapped[datetime] = mapped_column(UTCDateTime)
    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    auto_submitted: Mapped[bool] = mapped_column(default=False)
    correct: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)  # percent
    result: Mapped[dict] = mapped_column(JSON, default=dict)  # per category and per difficulty breakdown, next-step advice
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
