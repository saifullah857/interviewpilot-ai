from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=str(Path(__file__).resolve().parents[2] / ".env"), extra="ignore")  # always apps/api/.env, whatever folder the server starts in

    app_env: Literal["development", "test", "production"] = "development"
    secret_key: str = ""
    database_url: str = "sqlite:///./dev.db"
    cors_origins: str = "http://localhost:5173"
    access_token_minutes: int = 15
    refresh_token_days: int = 14
    login_max_attempts: int = 5
    login_window_seconds: int = 900
    signup_max_per_hour: int = 10
    # files
    storage_path: str = "./storage_private"
    max_upload_mb: int = 5
    max_resumes_per_user: int = 10
    uploads_per_hour: int = 10
    parse_timeout_seconds: int = 20
    # AI provider (Groq). Leave the key empty to run without AI; uploads and text extraction still work.
    llm_provider: Literal["groq", "fake"] = "groq"
    groq_api_key: str = ""
    groq_base_url: str = "https://api.groq.com/openai/v1"
    llm_model_primary: str = ""
    llm_model_fallback: str = "llama-3.3-70b-versatile"  # tried once when the primary model is rate limited or down; ignored if unavailable
    llm_timeout_seconds: int = 90
    llm_max_output: int = 4096
    llm_reasoning_effort: str = "low"  # only sent to gpt-oss models
    llm_retries: int = 2
    analyses_per_hour: int = 10
    # company research (Tavily). Leave the key empty to run without live research.
    research_provider: Literal["tavily", "fake"] = "tavily"
    tavily_api_key: str = ""
    tavily_base_url: str = "https://api.tavily.com"
    research_timeout_seconds: int = 30
    research_max_searches: int = 7
    research_max_extract_urls: int = 8
    research_max_sources: int = 10
    research_cache_days: int = 7
    research_runs_per_hour: int = 10
    research_page_chars: int = 15000
    # assessments
    assessments_per_hour: int = 12
    max_assessments_per_user: int = 30
    assessment_grace_seconds: int = 30
    # coding. local (default) runs code on this computer inside the API; http talks to the separate runner service; mock runs NO code.
    runner_mode: Literal["mock", "http", "local"] = "local"  # real execution on this computer; only RUNNER_MODE=mock switches it off
    runner_url: str = "http://127.0.0.1:8100"
    runner_shared_secret: str = ""
    runner_timeout_seconds: int = 40
    coding_max_code_bytes: int = 20000
    coding_runs_per_session: int = 30
    coding_submits_per_problem: int = 5
    coding_runner_calls_per_hour: int = 120
    coding_grace_seconds: int = 30
    coding_feedback_per_hour: int = 10
    # voice interview
    interviews_per_hour: int = 4
    interview_ai_calls_per_hour: int = 200  # interviewer turns + evaluations
    max_interviews_per_user: int = 30
    interview_idle_minutes: int = 30  # an active session with no activity this long becomes "interrupted"
    interview_purge_hours: int = 24  # transcripts the user did not ask to keep are removed this long after the session ends
    interview_answer_max_chars: int = 4000
    # reports
    reports_per_hour: int = 10
    max_reports_per_user: int = 100

    @model_validator(mode="after")
    def _check_secret(self) -> "Settings":
        if len(self.secret_key) < 32 or self.secret_key.lower().startswith("change-me"):
            raise ValueError(
                "SECRET_KEY must be at least 32 characters and not a placeholder. Generate one with: "
                'python -c "import secrets; print(secrets.token_urlsafe(48))"'
            )
        if self.runner_mode == "http" and len(self.runner_shared_secret) < 32:
            raise ValueError("RUNNER_SHARED_SECRET must be at least 32 characters when RUNNER_MODE=http.")
        return self

    @property
    def cookie_secure(self) -> bool:
        return self.app_env == "production"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
