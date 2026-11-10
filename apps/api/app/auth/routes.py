from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import cookies, service
from app.auth.schemas import LoginIn, MeOut, SignupIn
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError, error_response
from app.core.rate_limit import login_limiter, signup_limiter
from app.core.security import DUMMY_HASH, hash_password, needs_rehash, verify_password
from app.models.audit import record
from app.models.user import User, UserProfile
from app.users.mapping import me_out

router = APIRouter(prefix="/auth", tags=["auth"])


def client_ip(request: Request) -> str:
    # X-Forwarded-For is deliberately NOT trusted: it can be spoofed unless a trusted proxy sets it.
    return request.client.host if request.client else "unknown"


@router.get("/csrf")
def csrf(request: Request, response: Response) -> dict:
    token = cookies.set_csrf_cookie(response, request.cookies.get(cookies.CSRF))
    return {"csrf_token": token}


@router.post("/signup", status_code=201, response_model=MeOut)
def signup(body: SignupIn, request: Request, response: Response, db: Session = Depends(get_db)):
    s = get_settings()
    key = f"signup:{client_ip(request)}"
    wait = signup_limiter.retry_after(key, s.signup_max_per_hour, 3600)
    if wait:
        raise AppError(429, "rate_limited", "Too many sign-ups. Try again later.", headers={"Retry-After": str(wait)})
    signup_limiter.add(key)
    if db.scalars(select(User.id).where(User.email == body.email)).first():
        raise AppError(409, "email_taken", "An account with this email already exists.")
    user = User(email=body.email, password_hash=hash_password(body.password))
    user.profile = UserProfile(display_name=body.display_name.strip())
    db.add(user)
    try:
        db.flush()
    except IntegrityError:  # two sign-ups racing on the same email
        db.rollback()
        raise AppError(409, "email_taken", "An account with this email already exists.") from None
    access, refresh = service.issue_session(db, user)
    record(db, "signup", user.id)
    db.commit()
    cookies.set_auth_cookies(response, access, refresh)
    return me_out(user)


@router.post("/login", response_model=MeOut)
def login(body: LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    s = get_settings()
    ip = client_ip(request)
    pair_key, ip_key = f"login:{ip}:{body.email}", f"login-ip:{ip}"
    wait = login_limiter.retry_after(pair_key, s.login_max_attempts, s.login_window_seconds) or login_limiter.retry_after(
        ip_key, s.login_max_attempts * 4, s.login_window_seconds
    )
    if wait:
        raise AppError(429, "rate_limited", "Too many failed attempts. Try again later.", headers={"Retry-After": str(wait)})

    user = db.scalars(select(User).where(User.email == body.email)).first()
    # Always run one hash verification so unknown emails take about as long as wrong passwords.
    ok = verify_password(user.password_hash if user else DUMMY_HASH, body.password)
    if not (user and ok and user.is_active):
        login_limiter.add(pair_key)
        login_limiter.add(ip_key)
        record(db, "login_failed", user.id if user else None)
        db.commit()
        raise AppError(401, "invalid_credentials", "Email or password is incorrect.")

    login_limiter.clear(pair_key)
    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
    access, refresh = service.issue_session(db, user)
    record(db, "login", user.id)
    db.commit()
    cookies.set_auth_cookies(response, access, refresh)
    return me_out(user)


@router.post("/refresh", response_model=MeOut)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    try:
        user, access, new_raw = service.rotate_refresh(db, request.cookies.get(cookies.REFRESH))
    except AppError as e:
        resp = error_response(e)
        cookies.clear_auth_cookies(resp)
        return resp
    cookies.set_auth_cookies(response, access, new_raw)
    return me_out(user)


@router.post("/logout", status_code=204)
def logout(request: Request, db: Session = Depends(get_db)):
    user_id = service.revoke_presented_token(db, request.cookies.get(cookies.REFRESH))
    if user_id:
        record(db, "logout", user_id)
    db.commit()
    resp = Response(status_code=204)
    cookies.clear_auth_cookies(resp)
    return resp
