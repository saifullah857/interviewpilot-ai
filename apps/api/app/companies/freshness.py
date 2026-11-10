"""Freshness policy (see docs/COMPANY_DATA_POLICY.md section 5). Pure functions so they are easy to test."""

from datetime import datetime, timedelta

OFFICE_DAYS, JOB_DAYS, REPORT_DAYS = 180, 30, 365


def limit_days(source_type: str) -> int:
    return {"job_posting": JOB_DAYS, "candidate_report": REPORT_DAYS}.get(source_type, OFFICE_DAYS)


def effective_label(label: str, source_type: str, retrieved_at: datetime, now: datetime) -> str:
    """A stored label stops being trusted once the evidence is older than its freshness limit."""
    if now - retrieved_at > timedelta(days=limit_days(source_type)):
        return "unverified_or_outdated"
    return label


def needs_recheck(last_verified_at: datetime | None, now: datetime) -> bool:
    return last_verified_at is None or now - last_verified_at > timedelta(days=OFFICE_DAYS)
