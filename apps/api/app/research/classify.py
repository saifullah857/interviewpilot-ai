"""Deterministic source classification. Neither the search provider nor the AI decides what counts as 'official'."""

import ipaddress
import re
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse

REPORT_SITES = {"glassdoor", "reddit", "ambitionbox", "quora", "teamblind"}
JOB_BOARDS = {"linkedin", "indeed", "rozee", "mustakbil", "bayt"}
# Sites that block bots or restrict reuse: we use only the short search snippet, never fetch the page.
NO_FETCH = REPORT_SITES | JOB_BOARDS | {"facebook", "instagram", "twitter", "x"}
_CAREER_WORDS = ("career", "join", "work-with-us", "workwithus")
_JOB_WORDS = ("job", "jobs", "vacancy", "vacancies", "opening", "openings", "position", "positions")


@dataclass(frozen=True)
class Classified:
    url: str
    host: str
    source_type: str
    label: str
    official: bool
    fetchable: bool


def host_of(url: str) -> str | None:
    try:
        p = urlparse(url.strip())
    except ValueError:
        return None
    if p.scheme not in ("http", "https") or not p.hostname:
        return None
    h = p.hostname.lower().rstrip(".")
    if h.startswith("www."):
        h = h[4:]
    if h == "localhost" or h.endswith((".local", ".internal", ".localhost")) or "." not in h:
        return None
    try:
        ipaddress.ip_address(h)
        return None  # raw IP addresses are never researched
    except ValueError:
        return h


def company_domain(website: str | None) -> str | None:
    return host_of(website) if website else None


def canonical_url(url: str) -> str | None:
    if host_of(url) is None:
        return None
    p = urlparse(url.strip())
    return urlunparse((p.scheme, p.netloc.lower(), p.path.rstrip("/") or "/", "", "", ""))


def is_official_host(host: str, domain: str | None) -> bool:
    """True for the company's own domain or its subdomains. Look-alikes (evil-acme.com, acme.com.evil.net) are not official."""
    return bool(domain) and (host == domain or host.endswith("." + domain))


def _has_site(host: str, names: set[str]) -> bool:
    return any(lbl in names for lbl in host.split("."))


def classify(url: str, domain: str | None) -> Classified | None:
    host = host_of(url)
    canon = canonical_url(url)
    if host is None or canon is None:
        return None
    path = urlparse(canon).path.lower()
    segs = [s for s in re.split(r"[/_\-]", path) if s]
    fetchable = not _has_site(host, NO_FETCH)
    if is_official_host(host, domain):
        if any(w in path for w in _CAREER_WORDS) and not any(s in _JOB_WORDS for s in segs[1:]):
            stype = "careers_page"
        elif any(s in _JOB_WORDS for s in segs) and len(segs) >= 2:
            stype = "job_posting"
        else:
            stype = "official_website"
        return Classified(canon, host, stype, "official_verified", True, True)
    if _has_site(host, REPORT_SITES):
        return Classified(canon, host, "candidate_report", "public_candidate_report", False, False)
    if _has_site(host, JOB_BOARDS):
        return Classified(canon, host, "job_posting", "unverified_or_outdated", False, False)
    return Classified(canon, host, "other", "unverified_or_outdated", False, fetchable)
