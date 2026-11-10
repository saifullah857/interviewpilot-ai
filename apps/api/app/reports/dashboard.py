"""Everything the progress dashboard draws, for ONE user, computed from their own saved work."""

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.coding import CodingProblem, CodingSession
from app.models.report import Report
from app.models.screening import ScreeningSession
from app.models.user import User


def _pct(passed: int, total: int) -> int | None:
    return round(passed / total * 100) if total else None


def build(db: Session, user: User) -> dict:
    meta = {p.slug: p for p in db.scalars(select(CodingProblem)).all()}
    sessions = db.scalars(select(CodingSession).where(CodingSession.user_id == user.id, CodingSession.status == "submitted").order_by(CodingSession.submitted_at.asc()).limit(60)).all()

    coding, topic, difficulty, structure = [], defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0]), defaultdict(lambda: [0, 0])
    solved_slugs: set[str] = set()
    for s in sessions:
        final = {}
        for sub in s.submissions:  # the last real submit per problem is what counts
            if sub.kind == "submit":
                final[sub.problem_slug] = sub
        passed = total = solved = 0
        problems = []
        for slug in s.problem_slugs:
            sub = final.get(slug)
            m = meta.get(slug)
            ok = bool(sub and sub.executed)
            p, t = (sub.passed_count or 0, sub.total_count) if sub else (0, 0)
            if ok:
                passed, total = passed + p, total + t
                full = p == t
                solved += full
                if full:
                    solved_slugs.add(slug)
                if m:
                    for key in set(m.topics):
                        topic[key][0] += p
                        topic[key][1] += t
                    for key in set(m.ds or []):
                        structure[key][0] += p
                        structure[key][1] += t
                    difficulty[m.difficulty][0] += p
                    difficulty[m.difficulty][1] += t
            problems.append({"slug": slug, "title": m.title if m else slug, "difficulty": m.difficulty if m else "", "submitted": sub is not None, "executed": ok, "passed": p if ok else None, "total": t if ok else None, "score": _pct(p, t) if ok else None})
        executed = total > 0
        coding.append({
            "id": str(s.id), "date": s.submitted_at.isoformat() if s.submitted_at else None, "company": (s.plan or {}).get("company"),
            "score": _pct(passed, total) if executed else None, "passed": passed if executed else None, "total": total if executed else None,
            "solved": solved, "problems_count": len(s.problem_slugs), "executed": executed, "problems": problems,
        })

    def rows(d):
        return sorted(({"name": k, "passed": v[0], "total": v[1], "score": _pct(*v)} for k, v in d.items() if v[1]), key=lambda r: r["name"])

    topics = rows(topic)
    reports = db.scalars(select(Report).where(Report.user_id == user.id).order_by(Report.created_at.asc()).limit(60)).all()
    series = []
    for r in reports:
        comps = {c["key"]: c["value"] for c in (r.components or []) if c.get("status") == "available"}
        series.append({"id": str(r.id), "date": r.created_at.isoformat(), "role": r.role_slug, "overall": (r.overall or {}).get("value"), "components": comps, "auto": bool(r.auto)})

    tests = db.scalars(select(ScreeningSession).where(ScreeningSession.user_id == user.id, ScreeningSession.status == "submitted").order_by(ScreeningSession.submitted_at.asc()).limit(60)).all()
    screening = [{"id": str(t.id), "date": t.submitted_at.isoformat() if t.submitted_at else None, "score": t.score, "correct": t.correct, "total": t.total, "level": t.level, "company": (t.company_slug or None)} for t in tests]
    sc_cat: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for t in tests:
        for c in (t.result or {}).get("by_category", []):
            sc_cat[c["name"]][0] += c["correct"]
            sc_cat[c["name"]][1] += c["total"]
    sc_scores = [t["score"] for t in screening if t["score"] is not None]
    scored = [c["score"] for c in coding if c["score"] is not None]
    ranked = sorted((t for t in topics if t["total"] >= 3), key=lambda t: t["score"])
    return {
        "summary": {
            "coding_sessions": len(coding), "problems_solved": len(solved_slugs), "bank_size": len(meta), "reports": len(series),
            "average_coding_score": round(sum(scored) / len(scored)) if scored else None, "best_coding_score": max(scored) if scored else None,
            "screening_tests": len(screening), "average_screening_score": round(sum(sc_scores) / len(sc_scores)) if sc_scores else None,
            "latest_overall": next((s["overall"] for s in reversed(series) if s["overall"] is not None), None),
        },
        "coding": coding, "screening": screening, "screening_categories": rows(sc_cat), "topics": topics, "difficulty": rows(difficulty), "structures": rows(structure), "reports": series,
        "weak_topics": ranked[:3], "strong_topics": [t for t in reversed(ranked) if t["score"] >= 80][:3],
    }
