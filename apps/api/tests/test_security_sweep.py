"""Phase 10: checks that cover every route and the whole repository, so a new endpoint cannot quietly skip a protection."""

import re
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

from app.auth.deps import get_current_user
from app.core.config import Settings, get_settings
from app.main import create_app
from app.models.user import User
from tests.test_assessments import admin  # noqa: F401  (fixture)

ROOT = Path(__file__).resolve().parents[3]
API_DIR = ROOT / "apps" / "api"
UNSAFE = {"POST", "PUT", "PATCH", "DELETE"}
# The ONLY routes an anonymous visitor may call. Adding a route here is a security decision, so it must be deliberate.
OPEN_ROUTES = {
    ("GET", "/api/v1/health"),
    ("GET", "/api/v1/auth/csrf"),
    ("POST", "/api/v1/auth/signup"),
    ("POST", "/api/v1/auth/login"),
    ("POST", "/api/v1/auth/logout"),
}  # refresh is not here: without a valid refresh cookie it answers 401 like any protected route
# These end or replace the session, so a loop that reuses one login cannot call them.
SESSION_ROUTES = {("POST", "/api/v1/auth/logout"), ("POST", "/api/v1/auth/refresh"), ("DELETE", "/api/v1/me"), ("POST", "/api/v1/auth/login"), ("POST", "/api/v1/auth/signup")}
CANARY_GROQ, CANARY_TAVILY = "gsk_CANARYCANARYCANARYCANARY0001", "tvly-CANARYCANARY0002"


def routes():
    sch = create_app().openapi()
    return sorted((m.upper(), p) for p, v in sch["paths"].items() for m in v if m in ("get", "post", "put", "patch", "delete"))


def fill(path: str, value: str | None = None) -> str:
    def sub(m):
        if value is not None:
            return value
        return str(uuid.uuid4()) if m.group(1).endswith("_id") else "some-slug"

    return re.sub(r"\{([^}]+)\}", sub, path)


def send(api, method, path, *, csrf=True, body=None, raw=None):
    headers = api._headers(csrf)
    if raw is not None:
        return api.c.request(method, path, content=raw, headers={**headers, "Content-Type": "application/json"})
    return api.c.request(method, path, json=body if method in UNSAFE else None, headers=headers)


@pytest.fixture
def anon(api):
    return api


@pytest.fixture
def member(make_api):
    u = make_api()
    assert u.signup("member@example.com").status_code in (200, 201)
    return u


# ------------------------------------------------------------------ authentication and authorisation
def test_the_route_inventory_is_what_we_expect():
    r = routes()
    assert len(r) >= 70 and ("POST", "/api/v1/reports") in r and ("POST", "/api/v1/interviews") in r and ("GET", "/api/v1/health") in r


def test_only_the_deliberately_open_routes_answer_without_login(anon):
    open_found = set()
    for method, path in routes():
        r = send(anon, method, fill(path), body={})
        assert r.status_code < 500, (method, path, r.text)
        if r.status_code != 401:
            open_found.add((method, path))
    assert open_found == OPEN_ROUTES, f"unexpectedly open: {open_found - OPEN_ROUTES}; unexpectedly closed: {OPEN_ROUTES - open_found}"


def test_every_unauthenticated_denial_is_a_clean_401_with_no_detail(anon):
    for method, path in routes():
        if (method, path) in OPEN_ROUTES:
            continue
        r = send(anon, method, fill(path), body={})
        assert r.status_code == 401 and r.json()["error"]["code"] == "not_authenticated", (method, path, r.text)


def test_admin_routes_refuse_ordinary_members(member):
    admin_routes = [(m, p) for m, p in routes() if "/admin/" in p]
    assert len(admin_routes) >= 10
    for method, path in admin_routes:
        r = send(member, method, fill(path), body={})
        assert r.status_code == 403, (method, path, r.status_code, r.text)


def test_every_state_changing_route_needs_the_csrf_token(member):
    for method, path in routes():
        if method not in UNSAFE:
            continue
        r = send(member, method, fill(path), csrf=False, body={})
        assert r.status_code == 403 and r.json()["error"]["code"] == "csrf_failed", (method, path, r.status_code)


def test_a_wrong_csrf_token_is_refused(member):
    member._headers()
    r = member.c.post("/api/v1/reports", json={}, headers={"X-CSRF-Token": "x" * 40})
    assert r.status_code == 403 and r.json()["error"]["code"] == "csrf_failed"


# ------------------------------------------------------------------ robustness: no 500s, no leaks
def test_hostile_requests_never_cause_a_500_or_leak_internals(member, monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "groq_api_key", CANARY_GROQ)
    monkeypatch.setattr(s, "tavily_api_key", CANARY_TAVILY)
    allowed_503 = {"llm_not_configured", "llm_unavailable", "runner_unavailable", "research_unavailable"}
    checked = 0
    for method, path in routes():
        if (method, path) in SESSION_ROUTES or (method, path) in OPEN_ROUTES:
            continue
        for ident in (None, "not-a-uuid", "../../etc/passwd", "%00", "9" * 400):
            for body, raw in (({}, None), (None, b"{not json"), ({"x": [[[[1]]]] * 50, "text": "A" * 5000}, None), (None, b'"just a string"'), ({"text": "a\x00b", "name": "a\x00b", "code": "a\x00b", "display_name": "a\x00b"}, None), (None, b'{"text": "raw\x00nul"}')):
                r = send(member, method, fill(path, ident), body=body, raw=raw)
                text = r.text
                assert r.status_code < 500 or (r.status_code == 503 and r.json()["error"]["code"] in allowed_503), (method, path, ident, r.status_code, text[:200])
                for secret in ("Traceback", "site-packages", "/home/claude", CANARY_GROQ, CANARY_TAVILY, "sqlalchemy", "psycopg"):
                    assert secret not in text, (method, path, secret)
                checked += 1
    assert checked > 1000


def test_an_unexpected_exception_returns_a_generic_500_without_the_message(app, member):
    def boom():
        raise RuntimeError("db password is hunter2 at /srv/secret/path")

    app.dependency_overrides[get_current_user] = boom
    r = member.get("/me")
    app.dependency_overrides.clear()
    assert r.status_code == 500 and r.json()["error"]["code"] == "internal_error"
    assert "hunter2" not in r.text and "/srv/secret" not in r.text and "RuntimeError" not in r.text


def test_login_errors_do_not_reveal_whether_an_email_exists(anon, member):
    a = anon.login("member@example.com", "wrong password here 123")
    b = anon.login("nobody@example.com", "wrong password here 123")
    assert a.status_code == b.status_code == 401 and a.json() == b.json()


# ------------------------------------------------------------------ headers, cors, cookies, production mode
def test_every_response_carries_security_headers(anon, member):
    responses = [anon.get("/health"), anon.get("/me"), member.get("/me"), member.get("/reports/" + str(uuid.uuid4())), member.post("/reports", {"role": 5}), member.post("/reports", csrf=False), anon.c.get("/api/v1/nope")]
    assert {r.status_code for r in responses} >= {200, 401, 403, 404, 422}
    for r in responses:
        h = r.headers
        assert h["x-content-type-options"] == "nosniff" and h["x-frame-options"] == "DENY" and h["referrer-policy"] == "no-referrer"
        assert "frame-ancestors 'none'" in h["content-security-policy"] and h["cache-control"] == "no-store"


def test_cors_allows_only_the_configured_origin_and_never_a_wildcard(anon):
    assert "*" not in get_settings().cors_list
    ok = anon.c.options("/api/v1/me", headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173" and ok.headers.get("access-control-allow-credentials") == "true"
    evil = anon.c.options("/api/v1/me", headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in evil.headers
    evil_get = anon.c.get("/api/v1/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in evil_get.headers


def test_session_cookies_are_httponly_samesite_and_secure_when_configured(make_api, monkeypatch):
    monkeypatch.setattr(get_settings(), "app_env", "production")  # cookie_secure follows the environment
    assert get_settings().cookie_secure
    u = make_api()
    u.c.base_url = "https://testserver"  # Secure cookies are only sent back over https
    csrf = u.c.get("/api/v1/auth/csrf")
    r = u.signup("cookie@example.com")
    assert r.status_code in (200, 201), r.text
    jar = {c.split("=")[0]: c.lower() for c in [*csrf.headers.get_list("set-cookie"), *r.headers.get_list("set-cookie")]}
    for name in ("ip_access", "ip_refresh"):
        assert "httponly" in jar[name] and "samesite=lax" in jar[name] and "secure" in jar[name]
    assert "path=/api/v1/auth" in jar["ip_refresh"]
    assert "httponly" not in jar["ip_csrf"] and "secure" in jar["ip_csrf"]  # readable by the page on purpose


def test_production_hides_the_docs_and_refuses_weak_secrets(monkeypatch):
    s = get_settings()
    monkeypatch.setattr(s, "app_env", "production")
    from fastapi.testclient import TestClient

    c = TestClient(create_app())
    assert c.get("/docs").status_code == 404 and c.get("/openapi.json").status_code == 404
    r = c.get("/api/v1/health")
    assert "max-age" in r.headers["strict-transport-security"]
    for bad in ("", "short", "change-me" + "x" * 40):
        with pytest.raises(ValueError):
            Settings(secret_key=bad, _env_file=None)
    with pytest.raises(ValueError):
        Settings(secret_key="k" * 40, runner_mode="http", runner_shared_secret="short", _env_file=None)


# ------------------------------------------------------------------ the repository itself
def _files():
    skip = {"node_modules", ".git", "__pycache__", ".venv", "dist", ".pytest_cache", ".ruff_cache"}
    for p in ROOT.rglob("*"):
        if p.is_file() and not (set(p.parts) & skip) and p.suffix in {".py", ".ts", ".tsx", ".json", ".md", ".toml", ".ini", ".example", ".yml", ".yaml", ".js", ".html", ".css", ".txt", ""}:
            yield p


def test_no_real_looking_secrets_are_committed():
    pattern = re.compile(r"gsk_[A-Za-z0-9]{20,}|tvly-[A-Za-z0-9]{10,}|-----BEGIN (RSA |EC )?PRIVATE KEY-----|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{32,}")
    hits = []
    for p in _files():
        if p.name == "test_security_sweep.py":
            continue
        if pattern.search(p.read_text(errors="ignore")):
            hits.append(str(p.relative_to(ROOT)))
    assert hits == []


def test_env_files_are_ignored_and_the_example_holds_placeholders_only():
    ignore = (ROOT / ".gitignore").read_text()
    assert re.search(r"^\.env$", ignore, re.M) and ".env.*" in ignore and "!.env.example" in ignore
    assert not list(ROOT.rglob(".env")), "a real .env must never be inside the project tree that gets archived"
    for ex in ROOT.rglob(".env.example"):
        if "node_modules" in ex.parts:
            continue
        for line in ex.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, _, val = line.partition("=")
                if re.search(r"KEY|SECRET|PASSWORD|TOKEN", key, re.I):
                    assert val.strip() == "" or re.search(r"YOUR_|CHANGE|placeholder|example", val, re.I), (ex.name, key)


def test_the_main_process_has_no_dynamic_code_execution():
    banned = re.compile(r"\beval\(|\bexec\(|os\.system\(|shell\s*=\s*True|pickle\.loads?\(|yaml\.load\(|__import__\(|importlib\.import_module\(")
    for p in (API_DIR / "app").rglob("*.py"):
        assert not banned.search(p.read_text()), f"{p.relative_to(ROOT)} uses dynamic execution"
    users = [p.relative_to(API_DIR).as_posix() for p in (API_DIR / "app").rglob("*.py") if re.search(r"\bsubprocess\b", p.read_text())]
    assert users == ["app/resumes/files.py"], users  # the only child process is the resume parser: fixed argv, no shell, no secrets


def test_user_submitted_code_is_never_executed_by_the_api_process():
    src = "\n".join(p.read_text() for p in (API_DIR / "app" / "coding").rglob("*.py"))
    assert "compile(" not in src and "exec(" not in src and "subprocess" not in src
    assert "MockRunnerClient" in src and "HttpRunnerClient" in src  # code only ever goes to a runner client


def test_passwords_are_hashed_and_no_user_response_contains_a_hash(make_api, db):
    u = make_api()
    r = u.signup("hash@example.com")
    me = u.get("/me")
    row = db.scalars(select(User).where(User.email == "hash@example.com")).one()
    assert row.password_hash and "correct horse" not in row.password_hash and row.password_hash.startswith("$")
    for resp in (r, me):
        assert row.password_hash not in resp.text and "password" not in resp.text.lower().replace("password_changed", "")


# ------------------------------------------------------------------ NUL characters (PostgreSQL refuses them; SQLite accepts them silently)
def test_nul_in_a_path_or_query_is_a_clean_400_on_every_database(member, anon):
    for who in (member, anon):
        for url in ("/api/v1/coding/problems/%00", "/api/v1/coding/problems/a%00b", "/api/v1/companies?q=x%00y", "/api/v1/reports?role=%00"):
            r = who.c.get(url)
            assert r.status_code == 400 and r.json()["error"]["code"] == "invalid_input", (url, r.status_code)
            assert r.headers["x-content-type-options"] == "nosniff"  # rejections still carry the security headers


def test_nul_inside_json_text_is_refused_not_stored_and_not_a_server_error(anon, member, admin):  # noqa: F811
    assert anon.signup("nul@example.com", name="Ali\u0000").status_code == 422
    r = member.patch("/me", {"display_name": "Ali\x00 Khan"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_input"
    r = admin.post("/admin/companies", {"name": "Acme\x00 Soft"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_input"
    nested = member.patch("/me", {"display_name": "ok", "x": {"y": ["fine", "bad\x00"]}})
    assert nested.status_code == 422
    keyed = member.c.patch("/api/v1/me", content=b'{"bad\\u0000key": 1}', headers={**member._headers(), "Content-Type": "application/json"})
    assert keyed.status_code == 422 and keyed.json()["error"]["code"] == "invalid_input"


def test_a_literal_backslash_u0000_in_text_is_ordinary_text_and_is_allowed(member):
    r = member.patch("/me", {"display_name": "back\\u0000slash"})  # the characters \ u 0 0 0 0, not a NUL
    assert r.status_code == 200
    assert member.get("/me").json()["profile"]["display_name"] == "back\\u0000slash"


def test_invalid_json_and_raw_nul_bytes_get_the_normal_validation_error(member):
    h = {**member._headers(), "Content-Type": "application/json"}
    a = member.c.patch("/api/v1/me", content=b"{not json", headers=h)
    b = member.c.patch("/api/v1/me", content=b'{"display_name": "raw\x00nul"}', headers=h)
    assert a.status_code == 422 and b.status_code == 422


def test_oversized_json_bodies_are_refused(member):
    r = member.c.patch("/api/v1/me", content=b'{"display_name": "' + b"A" * 1_100_000 + b'"}', headers={**member._headers(), "Content-Type": "application/json"})
    assert r.status_code == 413 and r.json()["error"]["code"] == "too_large"


def test_a_database_data_error_becomes_a_422_and_never_a_500(app, member):
    from sqlalchemy.exc import DataError

    def boom():
        raise DataError("INSERT ...", {"secret": "hunter2"}, ValueError("PostgreSQL text fields cannot contain NUL"))

    app.dependency_overrides[get_current_user] = boom
    r = member.get("/me")
    app.dependency_overrides.clear()
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_input"
    assert "hunter2" not in r.text and "INSERT" not in r.text and "NUL" not in r.text
