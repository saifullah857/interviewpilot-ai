import uuid
from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.core.db import Base, UTCDateTime, utcnow


class AuditEvent(Base):
    """Security-relevant events. Holds no emails or other personal data; actor_id is nulled when a user is deleted."""

    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


def record(db: Session, action: str, actor_id: uuid.UUID | None = None, **detail) -> None:
    db.add(AuditEvent(actor_id=actor_id, action=action, detail=detail))
