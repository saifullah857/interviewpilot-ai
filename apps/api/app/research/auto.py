"""Self-service research for ordinary users: find the company's official domain, look for a Lahore office on official pages, and
(only when official evidence says so) mark the Lahore presence as confirmed by an AUTOMATIC check.

Honesty rules kept from the manual process:
  - a company is confirmed only when a page on its own domain mentions Lahore; the verification record says it was automatic (no human reviewer)
  - addresses are never invented: only a locality that appears in the page text is stored, otherwise just "Lahore"
  - candidate reports are labelled as such; unverified material is never activated"""

import re
import uuid

from sqlalchemy.orm import Session

from app.companies import service as company_service
from app.companies.schemas import DecisionIn, LocationIn
from app.core.errors import AppError
from app.models.company import Company, ResearchRun
from app.research import classify
from app.research.provider import BudgetedProvider, ResearchError
from app.resumes.text import normalize

LAHORE_LOCALITIES = [
    "Gulberg", "Johar Town", "DHA", "Model Town", "Garden Town", "Wapda Town", "Bahria Town", "Faisal Town", "Township", "Cavalry Ground",
    "Shadman", "Ferozepur Road", "Canal Road", "Mall Road", "Thokar Niaz Baig", "Niaz Baig", "Westwood Colony", "Sabzazar", "Iqbal Town",
    "Allama Iqbal Town", "Samanabad", "Liberty", "Kot Lakhpat", "Jail Road", "Lahore Cantt", "Cantt", "Defence", "Raiwind Road", "Valencia", "PECHS", "Bedian Road",
]
AGGREGATORS = {
    "clutch", "goodfirms", "techbehemoths", "crunchbase", "wikipedia", "facebook", "linkedin", "youtube", "instagram", "twitter", "x", "glassdoor",
    "indeed", "rozee", "mustakbil", "bayt", "ambitionbox", "reddit", "quora", "medium", "github", "yelp", "zoominfo", "apollo", "dnb", "owler",
    "pakwired", "worldorgs", "leadstal", "weekday", "mobileappdaily", "graana", "blogpakistan", "profilesinpk", "yellowpages", "lahore",
}
TWO_PART_TLDS = {"com.pk", "org.pk", "net.pk", "edu.pk", "co.uk", "com.au"}


def _key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _registrable(host: str, idx: int) -> str:
    parts = host.split(".")
    return ".".join(parts[idx:])


def discover_domain(research: BudgetedProvider, name: str) -> str | None:
    """Pick the search hit whose own domain looks like the company's name. Returns a bare domain such as 'acme.com'."""
    try:
        hits = research.search(f"{name} official website software company Lahore", max_results=8)
    except ResearchError:
        return None
    key, first = _key(name), _key(name.split()[0])
    for h in hits:
        host = classify.host_of(h.url)
        if not host:
            continue
        parts = host.split(".")
        if len(parts) < 2:
            continue
        tld_len = 2 if ".".join(parts[-2:]) in TWO_PART_TLDS else 1
        sld_idx = len(parts) - tld_len - 1
        if sld_idx < 0:
            continue
        label = _key(parts[sld_idx])
        if label in AGGREGATORS or any(p in AGGREGATORS for p in parts[:-1] if p != parts[sld_idx]):
            continue
        text = normalize(f"{h.title} {h.content}")
        named = normalize(name) in text
        match = label == key or (len(label) >= 6 and (key.startswith(label) or label.startswith(key))) or (len(first) >= 5 and label.startswith(first) and named)
        if match:
            return _registrable(host, sld_idx)
    return None


def _locality(text: str) -> str:
    low = text.lower()
    i = low.find("lahore")
    window = text[max(0, i - 300) : i + 300] if i >= 0 else text
    for loc in LAHORE_LOCALITIES:
        if re.search(rf"\b{re.escape(loc)}\b", window, re.IGNORECASE):
            return loc
    return "Lahore"


def apply_auto(db: Session, run: ResearchRun, company: Company, state: dict, summary: dict) -> None:
    """Confirm Lahore presence from official pages (if they say so) and approve this run's findings accordingly."""
    now_sources = {s.url: s for s in company.sources}
    official = [x for x in state.get("selected", []) if x.get("official") and "lahore" in (x.get("text") or "").lower()]
    summary["lahore_confirmed"] = False
    if official and company.verification_status != "verified_lahore":
        evidence = []
        for x in official[:3]:
            src = now_sources.get(x["url"])
            if src is None:
                continue
            src.supports_lahore = True
            src.excerpt = "Official page mentions a Lahore office (found by automated research; open the link to read it)."
            evidence.append(src.id)
        if evidence:
            if not any(loc.is_lahore for loc in company.locations):
                company_service.add_location(db, company, LocationIn(locality=_locality(official[0]["text"]), address=None, is_lahore=True))
            try:
                company_service.decide(
                    db, company, None,
                    DecisionIn(decision="verified", evidence_ids=[uuid.UUID(str(e)) for e in evidence],
                               notes="AUTOMATIC check by the research agent: a page on the company's own website mentions Lahore. Not reviewed by a person; re-check before relying on it."),
                )
            except AppError:
                pass
    if company.verification_status == "verified_lahore":
        summary["lahore_confirmed"] = True
        # approve this run's findings, but only from sources that are classified as official or as candidate reports
        for f in company.findings:
            if f.run_id == run.id and f.source.label in ("official_verified", "public_candidate_report") and f.status == "unreviewed":
                f.status = "active"
                if f.source.status == "unreviewed":
                    f.source.status = "active"
        summary["auto_approved"] = True
