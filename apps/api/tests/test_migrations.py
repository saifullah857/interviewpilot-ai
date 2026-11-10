import tempfile
from pathlib import Path

from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command

API_ROOT = Path(__file__).resolve().parents[1]


def test_migrations_upgrade_and_downgrade_cleanly():
    url = f"sqlite:///{Path(tempfile.mkdtemp()) / 'm.db'}"
    cfg = Config(str(API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(API_ROOT / "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    command.upgrade(cfg, "head")
    tables = set(inspect(create_engine(url)).get_table_names())
    assert {
        "users",
        "user_profiles",
        "refresh_tokens",
        "audit_events",
        "companies",
        "resumes",
        "resume_versions",
        "research_runs",
        "research_findings",
        "coding_problems",
        "coding_sessions",
        "coding_submissions",
        "research_sources",
        "interview_sessions",
        "interview_turns",
        "reports",
    } <= tables
    command.downgrade(cfg, "base")
    assert set(inspect(create_engine(url)).get_table_names()) <= {"alembic_version"}
