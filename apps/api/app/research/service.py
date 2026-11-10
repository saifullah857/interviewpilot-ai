import logging
import re
import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.companies import freshness
from app.companies import service as company_service
from app.core.config import get_settings
from app.core.db import get_engine, utcnow
from app.core.errors import AppError, not_found
from app.llm.base import LLMNotConfigured
from app.llm.factory import get_llm_provider
from app.models.audit import record
from app.models.company import Company, ResearchFinding, ResearchRun, ResearchSource
from app.models.user import User
from app.research import classify, workflow
from app.research.provider import BudgetedProvider, get_research_provider
from app.resumes import roles as role_catalog
from app.resumes.text import normalize

log = logging.getLogger("interviewpilot")
STALE_RUN_MINUTES = 10

# Hooks that tests replace.
build_research = get_research_provider
build_llm = get_llm_provider


def _finalize(run: ResearchRun, status: str, summary: dict, error_code: str | None = None) -> None:
    run.status, run.summary, run.error_code, run.finished_at = status, summary, error_code, utcnow()


def start_run(db: Session, company: Company, user: User, force: bool, auto: bool = False) -> tuple[ResearchRun, bool]:
    """Create a run (or return a recent cached one). The admin route researches verified Lahore companies only; the self-service
    route (auto=True) may also research a Lahore candidate, because confirming the Lahore office is part of its job."""
    if auto:
        if company.verification_status == "rejected":
            raise AppError(409, "company_rejected", "This company was rejected and cannot be researched.")
    elif company.verification_status != "verified_lahore" or not company_service.lahore_localities(company):
        raise AppError(409, "company_not_verified", "Only a verified Lahore company can be researched.")
    now = utcnow()
    for r in company.runs:
        if r.status == "running":
            if now - r.started_at > timedelta(minutes=STALE_RUN_MINUTES):
                _finalize(r, "failed", {"message": "The run did not finish."}, "timed_out")  # a crashed run must not block the company forever
            else:
                raise AppError(409, "research_in_progress", "Research is already running for this company.")
    s = get_settings()
    if not force:
        recent = [r for r in company.runs if r.status in ("succeeded", "partial") and now - r.created_at < timedelta(days=s.research_cache_days)]
        if recent:
            return recent[-1], True
    run = ResearchRun(company_id=company.id, requested_by=user.id, status="running", summary={})
    company.runs.append(run)
    db.flush()
    record(db, "research_started", user.id, company_id=str(company.id), run_id=str(run.id))
    return run, False


def _role_titles() -> list[str]:
    return [r["title"] for r in role_catalog.list_roles()]


def execute_run(run_id: uuid.UUID, auto: bool = False) -> None:
    """Background task. Opens its own session and always leaves the run in a final state."""
    with Session(get_engine()) as db:
        run = db.get(ResearchRun, run_id)
        if run is None:
            return
        try:
            company = company_service.get_by_id(db, run.company_id)
            s = get_settings()
            research = BudgetedProvider(build_research(), s.research_max_searches, s.research_max_extract_urls)
            try:
                llm = build_llm()
            except LLMNotConfigured:
                llm = None
            domain = classify.company_domain(company.website)
            discovered = False
            if domain is None and auto:
                from app.research import auto as auto_research

                found = auto_research.discover_domain(research, company.name)
                if found:
                    company.website, domain, discovered = f"https://{found}", found, True
                    db.commit()
            info = {"name": company.name, "domain": domain}
            state = workflow.run_graph(info, _role_titles(), research, llm, max_sources=s.research_max_sources, page_chars=s.research_page_chars)
            _persist(db, run, company, state, research, auto=auto, discovered=discovered)
        except Exception:  # noqa: BLE001 - the run must end in a final state whatever happens
            log.exception("Research run failed")
            db.rollback()
            run = db.get(ResearchRun, run_id)
            if run is not None:
                _finalize(run, "failed", {"message": "Research failed unexpectedly. Nothing was saved."}, "internal_error")
                db.commit()


MESSAGES = {
    "research_not_configured": "Live research isn't set up on this server (no search key). Nothing was changed.",
    "research_rate_limited": "The search provider is rate limiting us. Try again later. Nothing was changed.",
    "research_unavailable": "The search provider is unavailable. Nothing was changed; existing approved evidence is unaffected.",
}


def _persist(db: Session, run: ResearchRun, company: Company, state: dict, research: BudgetedProvider, auto: bool = False, discovered: bool = False) -> None:
    now = utcnow()
    stats = dict(state.get("stats", {}))
    summary: dict = {
        **stats,
        "searches_used": research.searches_used,
        "extracts_used": research.extracts_used,
        "warnings": list(state.get("warnings", [])),
        "conflicts": [],
        "injection_signals": {},
        "sources_saved": 0,
        "findings_saved": 0,
        "provider": research.name,
        "auto": auto,
        "website_discovered": discovered,
    }
    outcome = state.get("outcome")
    if outcome == "unavailable":
        code = state.get("error_code", "research_unavailable")
        summary["message"] = MESSAGES.get(code, MESSAGES["research_unavailable"])
        _finalize(run, "unavailable", summary, code)
        db.commit()
        return

    by_url = {s.url: s for s in company.sources}
    for sel in state.get("selected", []):
        src = by_url.get(sel["url"])
        if src is None:
            src = ResearchSource(
                company_id=company.id,
                url=sel["url"],
                source_type=sel["source_type"],
                label=sel["label"],
                supports_lahore=False,
                excerpt=f"Found by automated research ({sel['source_type']}). Open the link to review it.",
                retrieved_at=now,
                status="unreviewed",
                content_hash=sel.get("hash"),
                run_id=run.id,
            )
            company.sources.append(src)
            summary["sources_saved"] += 1
            by_url[sel["url"]] = src
        if sel.get("injection"):
            summary["injection_signals"][sel["url"]] = sel["injection"]
    db.flush()

    existing = {(f.source_id, f.kind, normalize(f.text)) for f in company.findings}
    for f in state.get("findings", []):
        src = by_url[f["url"]]
        key = (src.id, f["kind"], normalize(f["text"]))
        if key in existing:
            continue
        existing.add(key)
        company.findings.append(
            ResearchFinding(
                company_id=company.id,
                run_id=run.id,
                source_id=src.id,
                kind=f["kind"],
                role_title=(f["role_title"] or None),
                text=f["text"],
                skills=f["skills"],
                years_experience=f["years_experience"],
                scope=f["scope"],
                status="unreviewed",
                retrieved_at=now,
            )
        )
        summary["findings_saved"] += 1
    db.flush()
    if auto:
        from app.research import auto as auto_research

        auto_research.apply_auto(db, run, company, state, summary)
        db.flush()
    summary["conflicts"] = detect_conflicts(company)
    if outcome == "no_sources":
        summary["message"] = "No usable sources were found, so there is not enough public information to report."
    elif auto and not summary.get("lahore_confirmed"):
        summary["message"] = "No page on the company's own website mentioned a Lahore office, so its Lahore presence is NOT confirmed. Findings were saved but are hidden; practice stays general."
    elif summary["findings_saved"] == 0:
        summary["message"] = "Sources were found but no new findings could be confirmed in them. Review the sources manually."
    else:
        summary["message"] = (
            f"Saved {summary['findings_saved']} finding(s) from {len(state.get('selected', []))} source(s)."
            + (" Lahore office found on an official page and the findings are now shown with their source labels." if auto else " Review and approve before users can see them.")
        )
    _finalize(run, "succeeded" if summary["findings_saved"] > 0 else "partial", summary)
    record(db, "research_finished", run.requested_by, company_id=str(company.id), run_id=str(run.id), status=run.status)
    db.commit()


def detect_conflicts(company: Company) -> list[dict]:
    """Different 'years of experience' for the same role from different sources are reported, never silently resolved."""
    groups: dict[str, dict[int, set[str]]] = {}
    for f in company.findings:
        if f.kind != "role_requirement" or f.years_experience is None or f.status == "rejected" or not f.role_title:
            continue
        groups.setdefault(normalize(f.role_title), {}).setdefault(f.years_experience, set()).add(str(f.source_id))
    out = []
    for role, by_years in groups.items():
        if len(by_years) > 1:
            out.append({"role": role, "years": sorted(by_years), "sources": sorted({s for ids in by_years.values() for s in ids})})
    return out


def set_finding_status(db: Session, finding: ResearchFinding, status: str, actor: User) -> None:
    src = finding.source
    if status == "active":
        if src.status == "rejected":
            raise AppError(409, "source_rejected", "Its source was rejected. Re-open the source first.")
        if src.status == "unreviewed":
            src.status = "active"  # approving a finding is the reviewer accepting its source
    finding.status = status
    record(db, "finding_status_changed", actor.id, finding_id=str(finding.id), status=status)


def get_finding(db: Session, company_id: uuid.UUID, finding_id: uuid.UUID) -> ResearchFinding:
    f = db.scalars(select(ResearchFinding).where(ResearchFinding.id == finding_id, ResearchFinding.company_id == company_id)).first()
    if f is None:
        raise not_found("Finding")
    return f


def active_findings(company: Company) -> list[ResearchFinding]:
    return [f for f in company.findings if f.status == "active" and f.source.status == "active"]


def effective_label(f: ResearchFinding) -> str:
    return freshness.effective_label(f.source.label, f.source.source_type, f.retrieved_at, utcnow())


# ---------------- matching a resume against company evidence ----------------
GENERIC_TITLE_WORDS = {
    "junior",
    "senior",
    "intern",
    "internship",
    "engineer",
    "developer",
    "software",
    "associate",
    "trainee",
    "lead",
    "i",
    "ii",
    "iii",
    "the",
    "and",
    "of",
    "for",
    "a",
}
WEIGHTS = {"official_verified": 1.0, "public_candidate_report": 0.5, "unverified_or_outdated": 0.25}


def _title_tokens(title: str) -> set[str]:
    return {t for t in re.split(r"[^a-z0-9+#]+", title.lower()) if t and t not in GENERIC_TITLE_WORDS}


def title_matches(finding_title: str | None, role_title: str) -> bool:
    """Heuristic: a finding applies to a role when it is company-wide, generic ('Software Engineer'), or shares a distinctive word."""
    if not finding_title:
        return True
    ft = _title_tokens(finding_title)
    return not ft or bool(ft & _title_tokens(role_title))


def company_fit(parsed, role_slug: str, company: Company) -> dict:
    role = next((r for r in role_catalog._catalog()["roles"] if r["slug"] == role_slug), None)
    if role is None:
        raise not_found("Role")
    have = role_catalog._resume_skills(parsed)
    relevant = [f for f in active_findings(company) if f.kind in ("role_requirement", "tech_stack") and title_matches(f.role_title, role["title"])]
    base = {"company": {"slug": company.slug, "name": company.name}, "role": role["title"]}
    if not relevant:
        return {**base, "available": False, "reason": "No approved company evidence applies to this role yet, so only the general comparison is shown."}

    skills: dict[str, dict] = {}
    for f in relevant:
        label = effective_label(f)
        for raw in f.skills:
            k = role_catalog.canon(raw)
            if not k:
                continue
            entry = skills.setdefault(k, {"skill": k, "weight": 0.0, "reasons": [], "sources": []})
            entry["weight"] = max(entry["weight"], WEIGHTS[label])
            reason = (
                f"{'Official source' if label == 'official_verified' else 'Candidate report' if label == 'public_candidate_report' else 'Outdated or unverified source'}"
            )
            reason += (
                f" ({f.retrieved_at.date().isoformat()})" + (f" for {f.role_title}" if f.role_title else "") + ("" if f.scope == "lahore" else ", location not stated")
            )
            if reason not in entry["reasons"]:
                entry["reasons"].append(reason)
            if f.source.url not in {x["url"] for x in entry["sources"]}:
                entry["sources"].append({"url": f.source.url, "label": label})
    rows = []
    for e in sorted(skills.values(), key=lambda e: (-e["weight"], e["skill"])):
        h = have.get(e["skill"])
        rows.append({**e, "have": h[0] if h else None, "evidence": h[1] if h else ""})
    total = sum(r["weight"] for r in rows) or 1.0
    stated = sum(r["weight"] for r in rows if r["have"] == "stated")
    anyhave = sum(r["weight"] for r in rows if r["have"])
    notes = ["Weights: official source 1.0, candidate report 0.5, outdated or unverified 0.25. Scores are preparation hints, not hiring predictions."]
    if any(r["have"] == "inferred" for r in rows):
        notes.append("Some matches are inferred by the AI rather than written in your resume.")
    if any(f.scope != "lahore" for f in relevant):
        notes.append("Some evidence does not say it applies to the Lahore office.")
    if any(effective_label(f) == "unverified_or_outdated" for f in relevant):
        notes.append("Some evidence is older than its freshness limit and counts for less.")
    return {
        **base,
        "available": True,
        "skills": rows,
        "coverage_stated": round(stated / total, 2),
        "coverage_with_inferred": round(anyhave / total, 2),
        "evidence_count": len(relevant),
        "notes": notes,
    }
