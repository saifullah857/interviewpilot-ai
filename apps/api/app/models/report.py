import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, UTCDateTime, utcnow


class Report(Base):
    """An immutable snapshot. Scores are computed by the server from stored results at creation time and never edited afterwards;
    deleting a source (assessment, coding session, interview) leaves the report intact. Only the roadmap can be regenerated."""

    __tablename__ = "reports"
    __table_args__ = (
        CheckConstraint("mode in ('general','company')", name="mode_valid"),
        CheckConstraint("horizon in (7,30)", name="horizon_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    role_slug: Mapped[str] = mapped_column(String(80), index=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"), nullable=True)
    mode: Mapped[str] = mapped_column(String(8), default="general")
    resume_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True)
    assessment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("assessments.id", ondelete="SET NULL"), nullable=True)
    coding_session_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("coding_sessions.id", ondelete="SET NULL"), nullable=True)
    interview_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("interview_sessions.id", ondelete="SET NULL"), nullable=True)
    horizon: Mapped[int] = mapped_column(Integer, default=7)
    rubric_version: Mapped[str] = mapped_column(String(20))
    rubric: Mapped[dict] = mapped_column(JSON, default=dict)  # definitions and weights exactly as used for this report
    components: Mapped[list] = mapped_column(JSON, default=list)
    overall: Mapped[dict] = mapped_column(JSON, default=dict)
    gaps: Mapped[list] = mapped_column(JSON, default=list)
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    practice_questions: Mapped[list] = mapped_column(JSON, default=list)
    sources: Mapped[list] = mapped_column(JSON, default=list)  # approved company evidence, with URLs and labels
    roadmap: Mapped[dict] = mapped_column(JSON, default=dict)
    notes: Mapped[list] = mapped_column(JSON, default=list)
    auto: Mapped[bool] = mapped_column(Boolean, default=False)  # created by the app when the journey was finished, not by the user
    provider: Mapped[str] = mapped_column(String(40), default="")
    model: Mapped[str] = mapped_column(String(80), default="")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
