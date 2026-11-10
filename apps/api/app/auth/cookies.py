import secrets

from fastapi import Response

from app.core.config import get_settings

ACCESS, REFRESH, CSRF = "ip_access", "ip_refresh", "ip_csrf"
REFRESH_PATH = "/api/v1/auth"


def set_auth_cookies(resp: Response, access: str, refresh: str) -> None:
    s = get_settings()
    common = {"httponly": True, "secure": s.cookie_secure, "samesite": "lax"}
    resp.set_cookie(ACCESS, access, max_age=s.access_token_minutes * 60, path="/", **common)
    resp.set_cookie(REFRESH, refresh, max_age=s.refresh_token_days * 86400, path=REFRESH_PATH, **common)


def clear_auth_cookies(resp: Response) -> None:
    resp.delete_cookie(ACCESS, path="/")
    resp.delete_cookie(REFRESH, path=REFRESH_PATH)


def set_csrf_cookie(resp: Response, token: str | None = None) -> str:
    token = token or secrets.token_urlsafe(32)
    # Readable by JavaScript on purpose: the double-submit pattern needs the page to echo it in a header.
    resp.set_cookie(CSRF, token, httponly=False, secure=get_settings().cookie_secure, samesite="lax", path="/", max_age=86400 * 30)
    return token
