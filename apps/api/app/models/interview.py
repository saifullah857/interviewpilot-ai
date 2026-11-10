import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, UTCDateTime, utcnow


class InterviewSession(Base):
    """One practice interview. The transcript lives in InterviewTurn rows; `save_transcript` says whether they outlive the evaluation."""

    __tablename__ = "interview_sessions"
    __table_args__ = (
        CheckConstraint("status in ('active','completed','interrupted')", name="status_valid"),
        CheckConstraint("input_mode in ('voice','text')", name="input_mode_valid"),
        CheckConstraint("mode in ('general','company')", name="mode_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    resume_version_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("resume_versions.id", ondelete="SET NULL"), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    role_slug: Mapped[str] = mapped_column(String(80))
    mode: Mapped[str] = mapped_column(String(8), default="general")
    status: Mapped[str] = mapped_column(String(12), default="active")
    input_mode: Mapped[str] = mapped_column(String(8), default="text")
    question_target: Mapped[int] = mapped_column(Integer, default=6)
    plan: Mapped[dict] = mapped_column(JSON, default=dict)  # role brief + deterministic slots: what each main question should probe
    evidence: Mapped[list] = mapped_column(JSON, default=list)  # approved company evidence the interviewer may cite (numbered from 1)
    consent_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    save_transcript: Mapped[bool] = mapped_column(Boolean, default=False)
    transcript_purged_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    events: Mapped[list] = mapped_column(JSON, default=list)  # client signals such as mic_denied; capped
    evaluation: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # subjective AI evaluation, apart from any objective result
    provider: Mapped[str] = mapped_column(String(40), default="")
    model: Mapped[str] = mapped_column(String(80), default="")
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    last_activity_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    turns: Mapped[list["InterviewTurn"]] = relationship(back_populates="session", cascade="all, delete-orphan", order_by="InterviewTurn.position")


class InterviewTurn(Base):
    __tablename__ = "interview_turns"
    __table_args__ = (
        UniqueConstraint("session_id", "position"),
        CheckConstraint("speaker in ('interviewer','candidate')", name="speaker_valid"),
        CheckConstraint("kind in ('opening','question','follow_up','answer','skipped','closing')", name="kind_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_sessions.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    speaker: Mapped[str] = mapped_column(String(12))
    kind: Mapped[str] = mapped_column(String(10))
    text: Mapped[str] = mapped_column(Text)
    topic: Mapped[str | None] = mapped_column(String(60), nullable=True)
    slot: Mapped[int | None] = mapped_column(Integer, nullable=True)  # index of the plan slot this turn belongs to
    source: Mapped[str] = mapped_column(String(10), default="")  # candidate: typed | speech.  interviewer: ai | fallback | system
    informed_by: Mapped[list] = mapped_column(JSON, default=list)  # evidence numbers (interviewer turns only)
    flags: Mapped[list] = mapped_column(JSON, default=list)  # e.g. injection signals found in a candidate answer
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    session: Mapped[InterviewSession] = relationship(back_populates="turns")
