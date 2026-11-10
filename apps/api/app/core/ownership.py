from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.models.user import User

T = TypeVar("T")


def get_owned_or_404(db: Session, model: type[T], obj_id: UUID, user: User, owner_attr: str = "user_id") -> T:
    """Fetch a user-owned row. Another user's row looks exactly like a missing one (404, never 403),
    so IDs can't be probed. Every user-scoped query in later phases must go through this or an equivalent."""
    stmt = select(model).where(model.id == obj_id, getattr(model, owner_attr) == user.id)  # type: ignore[attr-defined]
    obj = db.scalars(stmt).first()
    if obj is None:
        raise not_found()
    return obj
