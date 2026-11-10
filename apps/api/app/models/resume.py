import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, UTCDateTime, utcnow


class Resume(Base):
    __tablename__ = "resumes"
    __table_args__ = (UniqueConstraint("user_id", "sha256", name="uq_resumes_user_sha"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filename: Mapped[str] = mapped_column(String(120))  # display only
    kind: Mapped[str] = mapped_column(String(8))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    pages: Mapped[int] = mapped_column(Integer, default=1)
    sha256: Mapped[str] = mapped_column(String(64))
    storage_key: Mapped[str] = mapped_column(String(32))
    text_content: Mapped[str] = mapped_column(Text)
    truncated: Mapped[bool] = mapped_column(Boolean, default=False)
    injection_signals: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    versions: Mapped[list["ResumeVersion"]] = relationship(back_populates="resume", cascade="all, delete-orphan", order_by="ResumeVersion.created_at")


class ResumeVersion(Base):
    """One AI analysis of a resume. Re-analysing creates a new version; old ones are kept for comparison."""

    __tablename__ = "resume_versions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), index=True)
    parsed_json: Mapped[dict] = mapped_column(JSON)
    report_json: Mapped[dict] = mapped_column(JSON, default=dict)
    schema_version: Mapped[str] = mapped_column(String(8))
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    resume: Mapped[Resume] = relationship(back_populates="versions")
