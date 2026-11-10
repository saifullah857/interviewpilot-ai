import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, UTCDateTime, utcnow


class BankQuestion(Base):
    """One question of the company-wise question bank. It is never presented as a real company interview question unless source_label says so."""

    __tablename__ = "bank_questions"
    __table_args__ = (
        CheckConstraint("kind in ('technical','scenario','mcq','output')", name="kind_valid"),
        CheckConstraint("difficulty in ('easy','medium','hard')", name="difficulty_valid"),
        CheckConstraint("source_label in ('verified','reported','company_focused_practice')", name="source_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    kind: Mapped[str] = mapped_column(String(12), index=True)
    category: Mapped[str] = mapped_column(String(40), index=True)
    difficulty: Mapped[str] = mapped_column(String(8))
    roles: Mapped[list] = mapped_column(JSON, default=list)
    companies: Mapped[list] = mapped_column(JSON, default=list)
    topics: Mapped[list] = mapped_column(JSON, default=list)
    prompt: Mapped[str] = mapped_column(Text)
    ideal_answer: Mapped[str] = mapped_column(Text, default="")
    key_points: Mapped[list] = mapped_column(JSON, default=list)
    follow_ups: Mapped[list] = mapped_column(JSON, default=list)
    options: Mapped[list] = mapped_column(JSON, default=list)  # mcq / output questions only
    answer_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, default="")
    source_label: Mapped[str] = mapped_column(String(32), default="company_focused_practice", index=True)
    source_note: Mapped[str] = mapped_column(String(300), default="")  # who reported it / where it was verified; required for verified and reported
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
