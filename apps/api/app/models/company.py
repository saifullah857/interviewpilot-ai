import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, UTCDateTime, utcnow

STATUSES = ("candidate", "pending_review", "verified_lahore", "stale", "rejected")
SOURCE_TYPES = ("official_website", "careers_page", "job_posting", "candidate_report", "registry", "other")
SOURCE_STATUSES = ("unreviewed", "active", "rejected")
LABELS = ("official_verified", "public_candidate_report", "unverified_or_outdated")  # ai_generated_practice never belongs to a research source
DECISIONS = ("verified", "rejected", "marked_stale")


def _in(col: str, values: tuple[str, ...]) -> str:
    return f"{col} in ({', '.join(repr(v) for v in values)})"


class Company(Base):
    __tablename__ = "companies"
    __table_args__ = (CheckConstraint(_in("verification_status", STATUSES), name="status_valid"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    website: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    careers_url: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    description: Mapped[str] = mapped_column(Text, default="")
    tech_focus: Mapped[list] = mapped_column(JSON, default=list)
    verification_status: Mapped[str] = mapped_column(String(20), default="candidate", index=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    locations: Mapped[list["CompanyLocation"]] = relationship(back_populates="company", cascade="all, delete-orphan", order_by="CompanyLocation.created_at")
    sources: Mapped[list["ResearchSource"]] = relationship(back_populates="company", cascade="all, delete-orphan", order_by="ResearchSource.created_at")
    findings: Mapped[list["ResearchFinding"]] = relationship(back_populates="company", cascade="all, delete-orphan", order_by="ResearchFinding.created_at")
    runs: Mapped[list["ResearchRun"]] = relationship(back_populates="company", cascade="all, delete-orphan", order_by="ResearchRun.created_at")
    verifications: Mapped[list["CompanyVerificationRecord"]] = relationship(
        back_populates="company", cascade="all, delete-orphan", order_by="CompanyVerificationRecord.created_at"
    )


class CompanyLocation(Base):
    __tablename__ = "company_locations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    locality: Mapped[str] = mapped_column(String(80))
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    is_lahore: Mapped[bool] = mapped_column(Boolean, default=True)
    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    company: Mapped[Company] = relationship(back_populates="locations")


class ResearchSource(Base):
    """One piece of evidence. Only sources a reviewer has activated are ever shown to users."""

    __tablename__ = "research_sources"
    __table_args__ = (
        UniqueConstraint("company_id", "url", name="uq_research_sources_company_url"),
        CheckConstraint(_in("label", LABELS), name="label_valid"),
        CheckConstraint(_in("source_type", SOURCE_TYPES), name="type_valid"),
        CheckConstraint(_in("status", SOURCE_STATUSES), name="status_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(2000))
    source_type: Mapped[str] = mapped_column(String(20))
    label: Mapped[str] = mapped_column(String(30))
    supports_lahore: Mapped[bool] = mapped_column(Boolean, default=False)
    excerpt: Mapped[str] = mapped_column(String(500), default="")  # short paraphrase, never copied text
    retrieved_at: Mapped[datetime] = mapped_column(UTCDateTime)
    status: Mapped[str] = mapped_column(String(12), default="unreviewed")
    added_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    company: Mapped[Company] = relationship(back_populates="sources")


class CompanyVerificationRecord(Base):
    __tablename__ = "company_verification_records"
    __table_args__ = (CheckConstraint(_in("decision", DECISIONS), name="decision_valid"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    decision: Mapped[str] = mapped_column(String(14))
    notes: Mapped[str] = mapped_column(Text, default="")
    evidence_ids: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    company: Mapped[Company] = relationship(back_populates="verifications")


RUN_STATUSES = ("running", "succeeded", "partial", "unavailable", "failed")
FINDING_KINDS = ("role_requirement", "tech_stack", "interview_format", "responsibility")
FINDING_STATUSES = ("unreviewed", "active", "rejected")
SCOPES = ("lahore", "unspecified")


class ResearchRun(Base):
    __tablename__ = "research_runs"
    __table_args__ = (CheckConstraint(_in("status", RUN_STATUSES), name="status_valid"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    requested_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(12), default="running")
    error_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    company: Mapped[Company] = relationship(back_populates="runs")


class ResearchFinding(Base):
    """A paraphrased fact found during research (never copied text). Hidden from users until an admin approves it."""

    __tablename__ = "research_findings"
    __table_args__ = (
        CheckConstraint(_in("kind", FINDING_KINDS), name="kind_valid"),
        CheckConstraint(_in("status", FINDING_STATUSES), name="status_valid"),
        CheckConstraint(_in("scope", SCOPES), name="scope_valid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id", ondelete="CASCADE"), index=True)
    run_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("research_runs.id", ondelete="SET NULL"), nullable=True)
    source_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("research_sources.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    role_title: Mapped[str | None] = mapped_column(String(100), nullable=True)
    text: Mapped[str] = mapped_column(String(300))
    skills: Mapped[list] = mapped_column(JSON, default=list)
    years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)
    scope: Mapped[str] = mapped_column(String(12), default="unspecified")
    status: Mapped[str] = mapped_column(String(12), default="unreviewed")
    retrieved_at: Mapped[datetime] = mapped_column(UTCDateTime)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)

    company: Mapped[Company] = relationship(back_populates="findings")
    source: Mapped[ResearchSource] = relationship()
