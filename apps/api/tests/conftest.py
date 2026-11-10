import os
import tempfile
from pathlib import Path

# Must be set before the app is imported.
os.environ["SECRET_KEY"] = "test-secret-key-that-is-long-enough-0123456789"
os.environ["APP_ENV"] = "test"
os.environ["RUNNER_MODE"] = "mock"  # the app default is the real local runner; tests must never execute code unless they ask
_TMP = tempfile.mkdtemp()
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{Path(_TMP) / 'test.db'}"
os.environ["DATABASE_URL"] = TEST_DB_URL
STORAGE_DIR = Path(_TMP) / "storage"
os.environ["STORAGE_PATH"] = str(STORAGE_DIR)
os.environ["LLM_PROVIDER"] = "fake"

import sys  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "services" / "sandbox-runner"))

import pytest  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import inspect, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from alembic import command  # noqa: E402
from app.core.db import Base, get_engine  # noqa: E402
from app.core.rate_limit import (  # noqa: E402
    analyze_limiter,
    assessment_limiter,
    coding_limiter,
    feedback_limiter,
    interview_ai_limiter,
    interview_limiter,
    login_limiter,
    report_limiter,
    research_limiter,
    signup_limiter,
    upload_limiter,
)
from app.main import create_app  # noqa: E402

API_ROOT = Path(__file__).resolve().parents[1]
PASSWORD = "correct horse battery"


@pytest.fixture(scope="session", autouse=True)
def migrated_db():
    cfg = Config(str(API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL)
    command.upgrade(cfg, "head")  # tests run against the real migrations
    yield


@pytest.fixture(autouse=True)
def _single_worker(monkeypatch):
    """The scripted test AIs keep counters and are not thread-safe, so tests generate one batch at a time."""
    monkeypatch.setattr("app.assessments.workflow.WORKERS", 1)


@pytest.fixture(autouse=True)
def clean_state(migrated_db):
    for lim in (login_limiter, signup_limiter, upload_limiter, analyze_limiter, research_limiter, assessment_limiter, coding_limiter, feedback_limiter, interview_limiter, interview_ai_limiter, report_limiter):
        lim.reset_all()
    yield
    if STORAGE_DIR.exists():
        for f in STORAGE_DIR.iterdir():
            f.unlink()
    engine = get_engine()
    existing = set(inspect(engine).get_table_names())  # test-only tables may not exist
    with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            if table.name in existing:
                conn.execute(text(f'DELETE FROM "{table.name}"'))


@pytest.fixture
def db():
    with Session(get_engine()) as s:
        yield s


class Api:
    """Test client that behaves like the browser: keeps cookies and echoes the CSRF token."""

    def __init__(self, app):
        self.c = TestClient(app, raise_server_exceptions=False)
        self.csrf: str | None = None

    def _headers(self, csrf: bool = True):
        if csrf and self.csrf is None:
            self.csrf = self.c.get("/api/v1/auth/csrf").json()["csrf_token"]
        return {"X-CSRF-Token": self.csrf} if csrf and self.csrf else {}

    def get(self, path, **kw):
        return self.c.get(f"/api/v1{path}", **kw)

    def post(self, path, json=None, csrf=True):
        return self.c.post(f"/api/v1{path}", json=json, headers=self._headers(csrf))

    def put(self, path, json=None, csrf=True):
        return self.c.put(f"/api/v1{path}", json=json, headers=self._headers(csrf))

    def patch(self, path, json=None, csrf=True):
        return self.c.patch(f"/api/v1{path}", json=json, headers=self._headers(csrf))

    def delete(self, path, json=None, csrf=True):
        return self.c.request("DELETE", f"/api/v1{path}", json=json, headers=self._headers(csrf))

    def upload(self, filename, data, csrf=True, path="/resumes"):
        return self.c.post(f"/api/v1{path}", files={"file": (filename, data, "application/octet-stream")}, headers=self._headers(csrf))

    def signup(self, email="ali@example.com", password=PASSWORD, name="Ali"):
        return self.post("/auth/signup", {"email": email, "password": password, "display_name": name})

    def login(self, email="ali@example.com", password=PASSWORD):
        return self.post("/auth/login", {"email": email, "password": password})


@pytest.fixture
def app():
    return create_app()


@pytest.fixture
def api(app):
    return Api(app)


@pytest.fixture
def make_api(app):
    return lambda: Api(app)
