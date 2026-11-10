import json
from functools import lru_cache
from pathlib import Path

from app.core.errors import not_found
from app.resumes.schemas import ParsedResume
from app.resumes.text import normalize

ROLES_FILE = Path(__file__).resolve().parents[4] / "data" / "roles" / "roles.json"
DISCLAIMER = "This compares your resume with a general skill list for the role. It is a preparation hint, not a prediction of being hired."


@lru_cache
def _catalog() -> dict:
    return json.loads(ROLES_FILE.read_text(encoding="utf-8"))


def list_roles() -> list[dict]:
    return [{"slug": r["slug"], "title": r["title"]} for r in _catalog()["roles"]]


def canon(skill: str) -> str:
    key = normalize(skill).strip(".,;:()")
    return _catalog()["aliases"].get(key, key)


def _resume_skills(p: ParsedResume) -> dict[str, tuple[str, str]]:
    """canonical skill -> (source, evidence). Stated beats inferred."""
    found: dict[str, tuple[str, str]] = {}

    def add(name: str, source: str, evidence: str) -> None:
        k = canon(name)
        if k and (k not in found or (source == "stated" and found[k][0] == "inferred")):
            found[k] = (source, evidence)

    for s in p.skills:
        add(s.name, s.source, s.evidence)
    for e in p.experience:
        for t in e.technologies:
            add(t, "stated", e.evidence)
    for pr in p.projects:
        for t in pr.technologies:
            add(t, "stated", pr.evidence)
    return found


def fit(parsed: ParsedResume, role_slug: str) -> dict:
    role = next((r for r in _catalog()["roles"] if r["slug"] == role_slug), None)
    if role is None:
        raise not_found("Role")
    have = _resume_skills(parsed)

    def group(skills: list[str]) -> dict:
        matched = [{"skill": s, "source": have[canon(s)][0], "evidence": have[canon(s)][1]} for s in skills if canon(s) in have]
        missing = [s for s in skills if canon(s) not in have]
        stated = sum(1 for m in matched if m["source"] == "stated")
        n = max(len(skills), 1)
        return {"matched": matched, "missing": missing, "coverage_stated": round(stated / n, 2), "coverage_with_inferred": round(len(matched) / n, 2)}

    req, pref = group(role["required"]), group(role["preferred"])
    notes = []
    if any(m["source"] == "inferred" for m in req["matched"] + pref["matched"]):
        notes.append("Some matches are inferred by the AI rather than written in your resume. Consider stating them explicitly if they are true.")
    if req["missing"]:
        notes.append("Missing skills are not necessarily missing from you. They are only missing from what your resume shows.")
    return {
        "role": {"slug": role["slug"], "title": role["title"]},
        "catalog_version": _catalog()["_meta"]["version"],
        "catalog_note": _catalog()["_meta"]["note"],
        "required": req,
        "preferred": pref,
        "notes": notes,
        "disclaimer": DISCLAIMER,
    }
