"""Suggests software houses and startups for a resume + role, and builds the self-service company view.
The ranking is a transparent heuristic (focus area + skill overlap), never a prediction of being hired."""

import json
from functools import lru_cache
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.companies import freshness
from app.companies.service import _load, lahore_localities
from app.core.db import utcnow
from app.models.company import Company
from app.research import service as research
from app.resumes import roles
from app.resumes.schemas import ParsedResume

PROFILES = Path(__file__).resolve().parents[4] / "data" / "company_seed" / "lahore_profiles.json"
STATUS_LABELS = {
    "verified_lahore": "Lahore presence confirmed",
    "stale": "Lahore presence needs a recheck",
    "candidate": "Lahore candidate: not checked yet",
    "pending_review": "Lahore candidate: awaiting review",
}
# role family -> {company family: weight}
AFFINITY: dict[str, dict[str, float]] = {
    "web": {"web": 1.0, "frontend": 1.0, "backend": 0.9, "mobile": 0.4},
    "frontend": {"frontend": 1.0, "web": 1.0, "mobile": 0.4, "backend": 0.3},
    "backend": {"backend": 1.0, "web": 0.9, "data": 0.4, "ai-ml": 0.3},
    "mobile": {"mobile": 1.0, "web": 0.4, "frontend": 0.4},
    "ai-ml": {"ai-ml": 1.0, "data": 0.6, "backend": 0.3},
    "data": {"data": 1.0, "ai-ml": 0.7, "backend": 0.3},
}
FAMILY_TITLES = {"web": "Web", "frontend": "Frontend", "backend": "Backend", "mobile": "Mobile", "ai-ml": "AI/ML", "data": "Data"}


@lru_cache
def _families() -> dict[str, list[str]]:
    try:
        return json.loads(PROFILES.read_text(encoding="utf-8")).get("families", {})
    except (OSError, ValueError):
        return {}


def role_catalog() -> list[dict]:
    return roles._catalog()["roles"]


def rank_roles(parsed: ParsedResume) -> list[dict]:
    out = []
    for r in role_catalog():
        f = roles.fit(parsed, r["slug"])
        score = round(100 * (0.7 * f["required"]["coverage_with_inferred"] + 0.3 * f["preferred"]["coverage_with_inferred"]))
        out.append(
            {
                "slug": r["slug"], "title": r["title"], "family": r.get("family", "backend"), "score": score,
                "matched": [m["skill"] for m in f["required"]["matched"] + f["preferred"]["matched"]][:8], "missing": f["required"]["missing"][:6],
            }
        )
    return sorted(out, key=lambda x: -x["score"])


def _company_skills(c: Company) -> set[str]:
    tags = {roles.canon(t) for t in (c.tech_focus or [])}
    for f in research.active_findings(c):
        tags |= {roles.canon(s) for s in (f.skills or [])}
    return {t for t in tags if t}


def item(c: Company, role: dict | None = None, have: set[str] | None = None) -> dict:
    fams = _families().get(c.slug, [])
    out = {
        "slug": c.slug,
        "name": c.name,
        "status": c.verification_status,
        "status_label": STATUS_LABELS.get(c.verification_status, c.verification_status),
        "localities": lahore_localities(c),
        "tech_focus": list(c.tech_focus or []),
        "focus_areas": [FAMILY_TITLES.get(f, f) for f in fams],
        "website": c.website,
        "last_verified_at": c.last_verified_at,
        "needs_recheck": freshness.needs_recheck(c.last_verified_at, utcnow()),
        "researched": bool(research.active_findings(c)),
        "match": None,
    }
    if role is not None:
        aff = AFFINITY.get(role.get("family", "backend"), {})
        fam_score = max([aff.get(f, 0.0) for f in fams] or [0.0])
        tags = _company_skills(c)
        overlap = sorted((have or set()) & tags)
        skill_score = min(1.0, len(overlap) / 3)
        score = round(100 * (0.6 * fam_score + 0.4 * skill_score))
        reasons = []
        if fam_score >= 0.9:
            reasons.append(f"Works in {', '.join(FAMILY_TITLES.get(f, f) for f in fams if aff.get(f, 0) >= 0.9)}, which fits {role['title']} roles")
        elif fam_score > 0:
            reasons.append("Partly related to this role's field")
        if overlap:
            reasons.append(f"Your resume shows: {', '.join(overlap[:5])}")
        out["match"] = {"score": score, "reasons": reasons, "basis": "Focus areas are rough project notes until the company is researched; this is a hint, not a prediction."}
    return out


def recommendations(db: Session, parsed: ParsedResume, role_slug: str | None, q: str | None = None) -> dict:
    ranked = rank_roles(parsed)
    chosen = next((r for r in ranked if r["slug"] == role_slug), ranked[0])
    have = set(roles._resume_skills(parsed))
    rows = _load(db, select(Company).where(Company.verification_status != "rejected").order_by(Company.name)).all()
    if q:
        n = q.lower()
        rows = [c for c in rows if n in c.name.lower() or any(n in t.lower() for t in (c.tech_focus or []))]
    items = [item(c, chosen, have) for c in rows]
    items.sort(key=lambda i: (-(i["match"]["score"] if i["match"] else 0), 0 if i["status"] == "verified_lahore" else 1, i["name"]))
    return {"roles": ranked, "role": chosen, "companies": items}


def detail(c: Company) -> dict:
    from app.companies import mapping

    d = mapping.detail(c).model_dump(mode="json")
    runs = [r for r in c.runs if r.status in ("running", "succeeded", "partial", "unavailable", "failed")]
    last = runs[-1] if runs else None
    auto_verified = any(v.decision == "verified" and v.reviewer_id is None for v in c.verifications) and c.verification_status == "verified_lahore"
    return {
        **d,
        "status": c.verification_status,
        "status_label": STATUS_LABELS.get(c.verification_status, c.verification_status),
        "auto_verified": auto_verified,
        "focus_areas": [FAMILY_TITLES.get(f, f) for f in _families().get(c.slug, [])],
        "latest_run": None if last is None else {"id": str(last.id), "status": last.status, "error_code": last.error_code, "summary": last.summary or {}, "started_at": last.started_at, "finished_at": last.finished_at},
        "focus_note": "Technology tags are rough project notes until research confirms them." if not research.active_findings(c) else None,
    }


def list_all(db: Session, q: str | None = None, family: str | None = None) -> list[dict]:
    """Every non-rejected company with its honest status. Candidates are clearly marked as not yet checked."""
    rows = _load(db, select(Company).where(Company.verification_status != "rejected").order_by(Company.name)).all()
    if q:
        n = q.lower()
        rows = [c for c in rows if n in c.name.lower() or any(n in t.lower() for t in (c.tech_focus or []))]
    items = [item(c) for c in rows]
    if family:
        want = FAMILY_TITLES.get(family, family)
        items = [i for i in items if want in i["focus_areas"]]
    items.sort(key=lambda i: (0 if i["status"] == "verified_lahore" else 1, i["name"]))
    return items
