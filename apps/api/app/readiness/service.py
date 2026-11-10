from sqlalchemy import select
from sqlalchemy.orm import Session

from app.coding import focus
from app.core.errors import not_found
from app.models.coding import CodingProblem
from app.models.screening import ScreeningSession
from app.models.user import User
from app.questions import service as qs
from app.readiness import engine
from app.resumes import roles


def _gap_rows(role: dict, parsed, evidence: dict, coding_avg: int | None) -> list[dict]:
    have = roles._resume_skills(parsed) if parsed is not None else {}
    rows = []
    for skills, importance in ((role["required"], "required"), (role["preferred"], "preferred")):
        for s in skills:
            k = roles.canon(s)
            cat = engine.SKILL_CATEGORY.get(k)
            ev = evidence.get(cat) if cat else None
            pct, src = (ev["score"], "screening") if ev and ev["total"] >= 2 else (None, None)
            if pct is None and k in ("data structures", "algorithms") and coding_avg is not None:
                pct, src = coding_avg, "coding"
            status = ("good" if pct >= 75 else "improve" if pct >= 40 else "weak") if pct is not None else "resume_only" if k in have else "not_shown"
            rows.append({"skill": s, "importance": importance, "status": status, "score": pct, "evidence_source": src, "on_resume": k in have, "category": cat})
    return rows


STATUS_TEXT = {"good": "Strong (assessed)", "improve": "Improve (assessed)", "weak": "Weak (assessed)", "resume_only": "Stated on resume, not assessed", "not_shown": "Not assessed and not on resume"}


def _next_actions(db: Session, user: User, role_slug: str, company: str | None, rows: list[dict], res: dict, level: str, rp: dict) -> tuple[list[dict], list[dict], list[dict]]:
    actions: list[dict] = []
    weakest = sorted((r for r in rows if r["status"] in ("weak", "improve") and r["category"]), key=lambda r: r["score"])
    cats = list(dict.fromkeys(r["category"] for r in weakest))[:2]
    for r in weakest[:2]:
        actions.append({"type": "screening", "text": f"Practise {r['skill']}: take a {level} screening test and review the explanations.", "why": f"Your assessed score for {r['skill']} is {r['score']}%.", "params": {"role": role_slug, "company": company, "level": level}})
    for r in [x for x in rows if x["status"] == "not_shown" and x["importance"] == "required"][:2]:
        actions.append({"type": "resume", "text": f"Learn {r['skill']} or, if you already know it, add it to your resume with a project.", "why": f"{r['skill']} is required for this role and nothing shows it yet.", "params": {}})
    comp = {c["key"]: c for c in res["components"]}
    if comp["coding_correctness"]["value"] is None:
        actions.append({"type": "coding", "text": "Do a smart coding challenge for this company and submit your solutions.", "why": "Coding is the heaviest part of the score and has no result yet.", "params": {"role": role_slug, "company": company}})
    if comp["screening"]["value"] is None:
        actions.append({"type": "screening", "text": "Take a mixed online screening test to find your weak topics.", "why": "No finished screening test exists for this role.", "params": {"role": role_slug, "company": company, "level": "mixed"}})
    if comp["interview_performance"]["value"] is None:
        actions.append({"type": "interview", "text": "Practise one mock interview and read the feedback.", "why": "There is no interview result for this role yet.", "params": {}})
    if comp["technical_knowledge"]["value"] is None:
        actions.append({"type": "assessment", "text": "Take a practice assessment for this role.", "why": "There is no assessment result for this role yet.", "params": {"role": role_slug}})
    cw = focus.company_weights(company)
    problems = [p for p in db.scalars(select(CodingProblem)).all() if role_slug in p.roles]
    ranked = sorted(problems, key=lambda p: -focus.score(p, cw, rp["tags"])[0])[:3]
    coding = [{"slug": p.slug, "title": p.title, "difficulty": p.difficulty} for p in ranked]
    questions = []
    for c in cats or ["python"]:
        _, found = qs.search(db, company, role_slug, c, None, None, None, None, False, 3, 0)
        questions += [{"slug": q.slug, "category": q.category, "kind": q.kind, "difficulty": q.difficulty, "prompt": q.prompt.split("\n")[0][:140]} for q in found]
    return actions[:6], coding, questions[:5]


def report(db: Session, user: User, role_slug: str, company: str | None, resume_id) -> dict:
    prof = focus.company_profile(company) if company else None
    if company and prof is None:
        raise not_found("Company")
    parsed, resume = engine.parsed_resume(db, user, resume_id)
    res = engine.evaluate(db, user, role_slug, company, parsed)
    role = engine._catalog_role(role_slug)
    evidence = engine.category_evidence(db, user)
    rows = _gap_rows(role, parsed, evidence, engine._coding_average(db, user))
    last = db.scalars(select(ScreeningSession).where(ScreeningSession.user_id == user.id, ScreeningSession.status == "submitted").order_by(ScreeningSession.submitted_at.desc())).first()
    level = ((last.result or {}).get("next_step", {}) or {}).get("next_level", "easy") if last else "easy"
    actions, coding, questions = _next_actions(db, user, role_slug, company, rows, res, level if level in ("easy", "medium", "hard", "mixed") else "easy", focus.resume_profile(parsed))
    avail = [c for c in res["components"] if c["value"] is not None]
    return {
        "company": {"slug": prof["slug"], "name": prof["name"], "focus": prof["focus"], "label": focus.LABEL, "note": focus.DISCLAIMER} if prof else None,
        "role": res["role"], "resume": {"id": str(resume.id), "filename": resume.filename} if resume is not None else None,
        "overall": res["overall"], "evidence_count": res["evidence_count"], "components": res["components"],
        "strengths": [c["name"] for c in avail if c["value"] >= 75], "weak_areas": [c["name"] for c in avail if c["value"] < 50],
        "skill_gap": [{**r, "status_text": STATUS_TEXT[r["status"]]} for r in rows],
        "next_actions": actions, "suggested_coding": coding, "suggested_questions": questions, "disclaimer": engine.DISCLAIMER,
    }


def role_matches(db: Session, user: User, company: str | None, resume_id) -> dict:
    if company and focus.company_profile(company) is None:
        raise not_found("Company")
    parsed, _ = engine.parsed_resume(db, user, resume_id)
    out = []
    for r in roles.list_roles():
        e = engine.evaluate(db, user, r["slug"], company, parsed)
        sm = e["skill_match"] or {"matched": [], "missing": []}
        out.append({"role": r, "value": e["overall"]["value"], "label": e["overall"]["label"], "confidence": e["overall"]["confidence"], "evidence_count": e["evidence_count"], "matching_skills": [m["skill"] for m in sm["matched"]][:6], "missing_required": [m["skill"] for m in sm["missing"] if m["required"]][:6]})
    out.sort(key=lambda x: -(x["value"] if x["value"] is not None else -1))
    return {"items": out, "has_resume": parsed is not None, "disclaimer": engine.DISCLAIMER}


def company_matches(db: Session, user: User, role_slug: str, resume_id) -> dict:
    parsed, _ = engine.parsed_resume(db, user, resume_id)
    out = []
    for p in focus.company_profiles():
        e = engine.evaluate(db, user, role_slug, p["slug"], parsed)
        sm = e["skill_match"] or {"matched": [], "missing": []}
        out.append({"company": {"slug": p["slug"], "name": p["name"]}, "focus": p["focus"], "value": e["overall"]["value"], "label": e["overall"]["label"], "confidence": e["overall"]["confidence"], "evidence_count": e["evidence_count"], "matching_skills": [m["skill"] for m in sm["matched"]][:6], "missing_required": [m["skill"] for m in sm["missing"] if m["required"]][:6]})
    out.sort(key=lambda x: -(x["value"] if x["value"] is not None else -1))
    return {"role": engine._catalog_role(role_slug)["title"], "items": out, "has_resume": parsed is not None, "disclaimer": engine.DISCLAIMER, "focus_note": focus.DISCLAIMER}
