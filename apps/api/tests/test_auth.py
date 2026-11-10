from datetime import timedelta

import jwt
import pytest
from sqlalchemy import select

from app.core.config import Settings
from app.core.db import utcnow
from app.core.security import create_access_token, decode_access_token, hash_password
from app.models.audit import AuditEvent
from app.models.user import RefreshToken, User
from tests.conftest import PASSWORD


def test_health_reports_database(api):
    r = api.get("/health")
    assert r.status_code == 200 and r.json() == {"status": "ok", "database": "ok"}


def test_signup_creates_user_with_argon2id_hash_and_httponly_cookies(api, db):
    r = api.signup()
    assert r.status_code == 201
    body = r.json()
    assert body["email"] == "ali@example.com" and body["profile"]["display_name"] == "Ali"
    assert "password" not in str(body).lower().replace("password_", "")
    user = db.scalars(select(User)).one()
    assert user.password_hash.startswith("$argon2id$") and PASSWORD not in user.password_hash
    set_cookie = " ".join(r.headers.get_list("set-cookie")).lower()
    assert "ip_access=" in set_cookie and "ip_refresh=" in set_cookie
    for name in ("ip_access", "ip_refresh"):
        line = next(c for c in r.headers.get_list("set-cookie") if c.startswith(name))
        assert "httponly" in line.lower() and "samesite=lax" in line.lower()


def test_signup_duplicate_email_is_case_insensitive(api):
    assert api.signup("Ali@Example.com").status_code == 201
    r = api.signup("ali@example.COM")
    assert r.status_code == 409 and r.json()["error"]["code"] == "email_taken"


@pytest.mark.parametrize("payload", [
    {"email": "not-an-email", "password": PASSWORD},
    {"email": "a@example.com", "password": "short"},
    {"email": "a@example.com", "password": "x" * 129},
])
def test_signup_validation(api, payload):
    r = api.post("/auth/signup", payload)
    assert r.status_code == 422
    err = r.json()["error"]
    assert err["code"] == "validation_error" and err["details"]


def test_state_changing_calls_need_csrf_token(api):
    r = api.post("/auth/signup", {"email": "a@example.com", "password": PASSWORD}, csrf=False)
    assert r.status_code == 403 and r.json()["error"]["code"] == "csrf_failed"
    api.get("/auth/csrf")  # cookie set, but header still missing
    r = api.post("/auth/login", {"email": "a@example.com", "password": PASSWORD}, csrf=False)
    assert r.status_code == 403


def test_wrong_csrf_header_is_rejected(api):
    api.get("/auth/csrf")
    r = api.c.post("/api/v1/auth/login", json={"email": "a@b.co", "password": "x"}, headers={"X-CSRF-Token": "forged"})
    assert r.status_code == 403


def test_login_success_then_me(api):
    api.signup()
    other = api.__class__(api.c.app)
    r = other.login()
    assert r.status_code == 200
    me = other.get("/me")
    assert me.status_code == 200 and me.json()["email"] == "ali@example.com"


def test_login_failures_share_one_message_for_unknown_email_and_wrong_password(api):
    api.signup()
    other = api.__class__(api.c.app)
    wrong = other.login(password="wrong password 1")
    unknown = other.login(email="nobody@example.com")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json()


def test_login_is_rate_limited_after_repeated_failures(api):
    api.signup()
    other = api.__class__(api.c.app)
    for _ in range(5):
        assert other.login(password="bad password 123").status_code == 401
    r = other.login(password="bad password 123")
    assert r.status_code == 429 and int(r.headers["retry-after"]) > 0
    assert other.login().status_code == 429  # even the right password waits out the lock


def test_signup_is_rate_limited(api):
    for i in range(10):
        assert api.signup(f"user{i}@example.com").status_code == 201
    assert api.signup("user11@example.com").status_code == 429


def test_me_requires_login(api):
    r = api.get("/me")
    assert r.status_code == 401 and r.json()["error"]["code"] == "not_authenticated"


def test_expired_or_forged_access_tokens_are_rejected(api, db):
    api.signup()
    user = db.scalars(select(User)).one()
    expired = create_access_token(user.id, timedelta(seconds=-5))
    api.c.cookies.delete("ip_access")  # drop the real cookie first, or the jar holds two and the valid one may be sent
    api.c.cookies.set("ip_access", expired, path="/")
    assert api.get("/me").status_code == 401
    claims = {"sub": str(user.id), "typ": "access", "exp": utcnow() + timedelta(minutes=5)}
    forged = jwt.encode(claims, "other-secret-" * 4, algorithm="HS256")
    api.c.cookies.delete("ip_access")
    api.c.cookies.set("ip_access", forged, path="/")
    assert api.get("/me").status_code == 401
    none_alg = jwt.encode({"sub": str(user.id), "typ": "access", "exp": utcnow() + timedelta(minutes=5)}, None, algorithm="none")
    assert decode_access_token(none_alg) is None


def test_inactive_user_loses_access(api, db):
    api.signup()
    user = db.scalars(select(User)).one()
    user.is_active = False
    db.commit()
    assert api.get("/me").status_code == 401
    assert api.login().status_code == 401


def test_refresh_rotates_token_and_old_one_is_dead(api):
    api.signup()
    old = api.c.cookies.get("ip_refresh", path="/api/v1/auth")
    assert api.post("/auth/refresh").status_code == 200
    new = api.c.cookies.get("ip_refresh", path="/api/v1/auth")
    assert new and new != old
    assert api.get("/me").status_code == 200


def test_refresh_reuse_revokes_the_whole_family(api, db):
    api.signup()
    stolen = api.c.cookies.get("ip_refresh", path="/api/v1/auth")
    assert api.post("/auth/refresh").status_code == 200  # legitimate rotation
    api.c.cookies.delete("ip_refresh")  # replace, don't add: two cookies with different domains would both exist
    api.c.cookies.set("ip_refresh", stolen, path="/api/v1/auth")  # attacker replays the old token
    assert api.post("/auth/refresh").status_code == 401
    assert all(t.revoked_at is not None for t in db.scalars(select(RefreshToken)))
    assert db.scalars(select(AuditEvent).where(AuditEvent.action == "refresh_reuse_detected")).first()


def test_expired_refresh_token_is_rejected(api, db):
    api.signup()
    rec = db.scalars(select(RefreshToken)).one()
    rec.expires_at = utcnow() - timedelta(minutes=1)
    db.commit()
    assert api.post("/auth/refresh").status_code == 401


def test_refresh_without_cookie_is_401(api):
    assert api.post("/auth/refresh").status_code == 401


def test_logout_revokes_refresh_token_and_clears_cookies(api, db):
    api.signup()
    r = api.post("/auth/logout")
    assert r.status_code == 204
    assert all(t.revoked_at is not None for t in db.scalars(select(RefreshToken)))
    assert api.get("/me").status_code == 401


def test_profile_and_consents_update_and_default_off(api):
    api.signup()
    assert api.get("/me/consents").json() == {"voice_transcript": False, "analytics": False}
    assert api.patch("/me/consents", {"voice_transcript": True}).json()["voice_transcript"] is True
    r = api.patch("/me", {"display_name": " Ali K ", "target_roles": ["Python Developer"]})
    assert r.json()["profile"]["display_name"] == "Ali K" and r.json()["profile"]["target_roles"] == ["Python Developer"]
    assert api.patch("/me", {"target_roles": [""]}).status_code == 422
    assert api.patch("/me", {"role": "admin"}).json()["role"] == "user"  # unknown fields can't grant privileges


def test_delete_account_requires_password_and_removes_everything(api, db):
    api.signup()
    assert api.delete("/me", {"password": "wrong password 1"}).status_code == 403
    assert api.delete("/me", {"password": PASSWORD}).status_code == 204
    assert db.scalars(select(User)).all() == [] and db.scalars(select(RefreshToken)).all() == []
    assert api.get("/me").status_code == 401
    assert api.login().status_code == 401
    events = db.scalars(select(AuditEvent)).all()
    assert "account_deleted" in [e.action for e in events] and all(e.actor_id is None for e in events if e.action == "account_deleted")


def test_audit_log_holds_no_email(api, db):
    api.signup()
    api.login()
    assert "ali@example.com" not in str([e.detail for e in db.scalars(select(AuditEvent))])


def test_unknown_route_and_method_use_error_shape(api):
    r = api.get("/nope")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


def test_unhandled_errors_do_not_leak_details(app):
    from tests.conftest import Api

    @app.get("/api/v1/boom")
    def boom():
        raise RuntimeError("secret-internal-detail /home/x/app.py")

    r = Api(app).get("/boom")
    assert r.status_code == 500
    assert r.json() == {"error": {"code": "internal_error", "message": "Something went wrong on our side."}}
    assert "secret-internal-detail" not in r.text and "Traceback" not in r.text


def test_hash_password_is_salted(db):
    assert hash_password("same password") != hash_password("same password")


def test_settings_reject_weak_secret():
    for bad in ("", "short", "change-me-" + "x" * 40):
        with pytest.raises(ValueError):
            Settings(secret_key=bad)


def test_cookie_secure_flag_follows_environment():
    assert Settings(secret_key="k" * 40, app_env="production").cookie_secure is True
    assert Settings(secret_key="k" * 40, app_env="development").cookie_secure is False


# ---------------------------------------------------------------- change password and admin reset (Phase 12)
NEW_PASSWORD = "a brand new passphrase 42"


def test_change_password_signs_other_devices_out_but_keeps_this_one(make_api, db):
    phone, laptop = make_api(), make_api()
    phone.signup("pw@example.com")
    assert laptop.login("pw@example.com").status_code == 200
    r = phone.post("/me/password", {"current_password": PASSWORD, "new_password": NEW_PASSWORD})
    assert r.status_code == 204
    assert phone.get("/me").status_code == 200  # this device got a fresh session
    # the other device's refresh token was revoked: it cannot renew its session
    assert laptop.post("/auth/refresh").status_code == 401
    # old password is dead, new one works
    other = make_api()
    assert other.login("pw@example.com", PASSWORD).status_code == 401
    assert other.login("pw@example.com", NEW_PASSWORD).status_code == 200
    events = db.scalars(select(AuditEvent).where(AuditEvent.action == "password_changed")).all()
    assert len(events) == 1 and NEW_PASSWORD not in str(events[0].detail) and PASSWORD not in str(events[0].detail)


def test_change_password_needs_the_current_password_and_changes_nothing_when_wrong(api, db):
    api.signup("pw2@example.com")
    r = api.post("/me/password", {"current_password": "not my password", "new_password": NEW_PASSWORD})
    assert r.status_code == 403 and r.json()["error"]["code"] == "wrong_password"
    assert api.login("pw2@example.com", PASSWORD).status_code == 200  # still the old password
    assert db.scalars(select(AuditEvent).where(AuditEvent.action == "password_change_failed")).first()


def test_change_password_validates_the_new_password(api):
    api.signup("pw3@example.com")
    assert api.post("/me/password", {"current_password": PASSWORD, "new_password": "short"}).status_code == 422
    assert api.post("/me/password", {"current_password": PASSWORD, "new_password": "x" * 129}).status_code == 422
    same = api.post("/me/password", {"current_password": PASSWORD, "new_password": PASSWORD})
    assert same.status_code == 422 and same.json()["error"]["code"] == "same_password"
    assert api.post("/me/password", {"current_password": PASSWORD, "new_password": NEW_PASSWORD, "extra": 1}).status_code == 422


def test_change_password_is_throttled_against_guessing_and_needs_login_and_csrf(api, make_api, monkeypatch):
    from app.core.config import get_settings

    anon = make_api()
    assert anon.post("/me/password", {"current_password": PASSWORD, "new_password": NEW_PASSWORD}).status_code == 401
    api.signup("pw4@example.com")
    assert api.post("/me/password", {"current_password": PASSWORD, "new_password": NEW_PASSWORD}, csrf=False).status_code == 403
    monkeypatch.setattr(get_settings(), "login_max_attempts", 3)
    for _ in range(3):
        assert api.post("/me/password", {"current_password": "wrong guess", "new_password": NEW_PASSWORD}).status_code == 403
    blocked = api.post("/me/password", {"current_password": PASSWORD, "new_password": NEW_PASSWORD})  # even the right one waits
    assert blocked.status_code == 429 and blocked.headers["Retry-After"]


def test_admin_cli_reset_password_signs_the_user_out_and_never_takes_the_password_as_an_argument(make_api, db, monkeypatch):
    from app import cli

    u, intruder = make_api(), make_api()
    u.signup("forgot@example.com")
    answers = iter([NEW_PASSWORD, NEW_PASSWORD])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(answers))
    assert cli.main(["reset-password", "forgot@example.com"]) == 0
    assert u.post("/auth/refresh").status_code == 401  # existing sessions are gone
    assert intruder.login("forgot@example.com", PASSWORD).status_code == 401
    assert intruder.login("forgot@example.com", NEW_PASSWORD).status_code == 200
    ev = db.scalars(select(AuditEvent).where(AuditEvent.action == "password_reset_by_admin")).one()
    assert NEW_PASSWORD not in str(ev.detail)
    with pytest.raises(SystemExit):
        cli.main(["reset-password", "forgot@example.com", "extra-positional-argument"])  # a password on the command line is not even accepted


def test_admin_cli_reset_password_refuses_unknown_users_mismatches_and_weak_passwords(make_api, monkeypatch, capsys):
    from app import cli

    make_api().signup("known@example.com")
    assert cli.main(["reset-password", "nobody@example.com"]) == 1
    monkeypatch.setattr("getpass.getpass", lambda prompt="": "short")
    assert cli.main(["reset-password", "known@example.com"]) == 1
    answers = iter([NEW_PASSWORD, "something else entirely"])
    monkeypatch.setattr("getpass.getpass", lambda prompt="": next(answers))
    assert cli.main(["reset-password", "known@example.com"]) == 1
    err = capsys.readouterr().err
    assert "No user" in err and "8 to 128" in err and "do not match" in err
    assert make_api().login("known@example.com", PASSWORD).status_code == 200  # nothing changed
