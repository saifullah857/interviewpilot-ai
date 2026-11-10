import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, UTCDateTime, utcnow


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role in ('user','admin')", name="role_valid"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)  # stored lower-case
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    display_name: Mapped[str] = mapped_column(String(100), default="")
    education_level: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_roles: Mapped[list] = mapped_column(JSON, default=list)
    consent_voice_transcript: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_analytics: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)

    user: Mapped[User] = relationship(back_populates="profile")


class RefreshToken(Base):
    """Server-side record of an opaque refresh token. Only the SHA-256 hash is stored."""

    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    family_id: Mapped[uuid.UUID] = mapped_column(Uuid, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    revoked_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
