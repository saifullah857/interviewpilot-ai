import uuid
from datetime import timedelta

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.db import utcnow
from app.core.errors import not_authenticated
from app.core.security import create_access_token, hash_password, hash_token, new_opaque_token
from app.models.audit import record
from app.models.user import RefreshToken, User


def issue_session(db: Session, user: User, family_id: uuid.UUID | None = None) -> tuple[str, str]:
    raw = new_opaque_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            family_id=family_id or uuid.uuid4(),
            token_hash=hash_token(raw),
            expires_at=utcnow() + timedelta(days=get_settings().refresh_token_days),
        )
    )
    return create_access_token(user.id), raw


def revoke_family(db: Session, family_id: uuid.UUID) -> None:
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )


def rotate_refresh(db: Session, raw: str | None) -> tuple[User, str, str]:
    """Exchange a refresh token for a new pair. Presenting an already-used token revokes the whole family."""
    if not raw:
        raise not_authenticated()
    rec = db.scalars(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw))).first()
    if rec is None:
        raise not_authenticated()
    if rec.revoked_at is not None:
        revoke_family(db, rec.family_id)
        record(db, "refresh_reuse_detected", rec.user_id)
        db.commit()
        raise not_authenticated()
    if rec.expires_at <= utcnow():
        raise not_authenticated()
    user = db.get(User, rec.user_id)
    if user is None or not user.is_active:
        raise not_authenticated()
    rec.revoked_at = utcnow()
    access, new_raw = issue_session(db, user, rec.family_id)
    db.commit()
    return user, access, new_raw


def revoke_presented_token(db: Session, raw: str | None) -> uuid.UUID | None:
    if not raw:
        return None
    rec = db.scalars(select(RefreshToken).where(RefreshToken.token_hash == hash_token(raw))).first()
    if rec is None:
        return None
    revoke_family(db, rec.family_id)
    return rec.user_id


def set_password(db: Session, user: User, new_password: str) -> None:
    """Replace the password and sign the account out everywhere: every refresh token of this user is revoked.
    Callers decide whether to start a fresh session afterwards. Used by the change-password endpoint and by the admin CLI."""
    user.password_hash = hash_password(new_password)
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id, RefreshToken.revoked_at.is_(None)).values(revoked_at=utcnow()))
