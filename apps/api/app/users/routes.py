from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import cookies
from app.auth import service as auth_service
from app.auth.deps import get_current_user
from app.auth.schemas import ChangePasswordIn, Consents, ConsentsPatch, DeleteMeIn, MeOut, ProfilePatch
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError
from app.core.rate_limit import login_limiter
from app.core.security import verify_password
from app.models.audit import record
from app.models.resume import Resume
from app.models.user import User
from app.storage.local import LocalStorage, get_storage
from app.users.mapping import me_out

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=MeOut)
def get_me(user: User = Depends(get_current_user)):
    return me_out(user)


@router.patch("", response_model=MeOut)
def patch_me(body: ProfilePatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = user.profile
    data = body.model_dump(exclude_unset=True)
    if "display_name" in data and data["display_name"] is not None:
        p.display_name = data["display_name"].strip()
    if "education_level" in data:
        p.education_level = (data["education_level"] or "").strip() or None
    if data.get("target_roles") is not None:
        p.target_roles = data["target_roles"]
    db.commit()
    return me_out(user)


@router.get("/consents", response_model=Consents)
def get_consents(user: User = Depends(get_current_user)):
    return me_out(user).consents


@router.patch("/consents", response_model=Consents)
def patch_consents(body: ConsentsPatch, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = user.profile
    if body.voice_transcript is not None:
        p.consent_voice_transcript = body.voice_transcript
    if body.analytics is not None:
        p.consent_analytics = body.analytics
    record(db, "consents_changed", user.id)
    db.commit()
    return me_out(user).consents


@router.post("/password", status_code=204)
def change_password(body: ChangePasswordIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Needs the current password again (a stolen session alone must not be enough). Signs every other device out and keeps this one signed in."""
    s = get_settings()
    key = f"pw:{user.id}"
    wait = login_limiter.retry_after(key, s.login_max_attempts, s.login_window_seconds)
    if wait:
        raise AppError(429, "rate_limited", "Too many failed attempts. Try again later.", headers={"Retry-After": str(wait)})
    if not verify_password(user.password_hash, body.current_password):
        login_limiter.add(key)
        record(db, "password_change_failed", user.id)
        db.commit()
        raise AppError(403, "wrong_password", "Your current password is incorrect.")
    if body.new_password == body.current_password:
        raise AppError(422, "same_password", "Choose a password that is different from the current one.")
    auth_service.set_password(db, user, body.new_password)
    access, refresh = auth_service.issue_session(db, user)  # a new session for this device only
    record(db, "password_changed", user.id)
    db.commit()
    resp = Response(status_code=204)
    cookies.set_auth_cookies(resp, access, refresh)
    return resp


@router.delete("", status_code=204)
def delete_me(body: DeleteMeIn, user: User = Depends(get_current_user), db: Session = Depends(get_db), storage: LocalStorage = Depends(get_storage)):
    """Permanently deletes the account and everything that cascades from it. Requires the password again."""
    if not verify_password(user.password_hash, body.password):
        raise AppError(403, "wrong_password", "Password is incorrect.")
    keys = list(db.scalars(select(Resume.storage_key).where(Resume.user_id == user.id)).all())
    db.delete(user)
    db.flush()
    record(db, "account_deleted")  # no actor id and no personal data by design
    db.commit()
    for k in keys:  # stored files are removed only after the account is gone from the database
        storage.delete(k)
    resp = Response(status_code=204)
    cookies.clear_auth_cookies(resp)
    return resp
