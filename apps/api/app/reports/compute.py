"""Turns stored results into scores, gaps and strengths. No AI is involved anywhere in this file, so nothing an AI says can change a number."""

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assessments import service as assessments
from app.coding import service as coding
from app.models.assessment import Assessment
from app.models.coding import CodingProblem, CodingSession
from app.models.interview import InterviewSession
from app.reports.rubric import BY_KEY, LOW_EVIDENCE_MCQ, OVERALL_HOW
from app.resumes import roles
from app.resumes.schemas import ParsedResume

SEVERITY = {"high": 0, "medium": 1, "low": 2}


def _component(key: str, status: str, value: int | None, reason: str = "", detail: dict | None = None, sources: list[str] | None = None, low_evidence: bool = False) -> dict:
    d = BY_KEY[key]
    return {
        "key": key, "name": d["name"], "kind": d["kind"], "weight": d["weight"], "status": status, "value": value, "reason": reason,
        "low_evidence": low_evidence, "detail": detail or {}, "sources": sources or [], "how": d["how"],
    }


@dataclass
class Inputs:
    role_slug: str
    parsed: ParsedResume | None = None
    assessment: Assessment | None = None
    coding: CodingSession | None = None
    interview: InterviewSession | None = None


def _gap(gaps: dict[str, dict], label: str, severity: str, kind: str, source: str, detail: str) -> None:
    g = gaps.setdefault(label.lower(), {"label": label, "severity": severity, "kind": kind, "evidence": []})
    if SEVERITY[severity] < SEVERITY[g["severity"]]:
        g["severity"] = severity
    if g["kind"] != kind:
        g["kind"] = "both"
    g["evidence"].append({"source": source, "detail": detail})


def compute(db: Session, i: Inputs) -> dict[str, Any]:
    comps: dict[str, dict] = {}
    gaps: dict[str, dict] = {}
    strengths: list[dict] = []
    practice: list[dict] = []
    notes: list[str] = []

    # ---- resume fit (objective, not in overall)
    if i.parsed is not None:
        fit = roles.fit(i.parsed, i.role_slug)
        req = fit["required"]
        total = len(req["matched"]) + len(req["missing"])
        comps["resume_fit"] = _component(
            "resume_fit", "available", round(req["coverage_stated"] * 100), detail={"matched": [m["skill"] for m in req["matched"]], "missing": list(req["missing"]), "total_required": total, "coverage_with_inferred": round(req["coverage_with_inferred"] * 100)},
            reason="Share of required skills your resume states. It is not a hiring probability.",
        )
        for s in req["missing"]:
            _gap(gaps, s, "high", "objective", "resume_fit", "A required skill that your resume does not show")
        for m in req["matched"]:
            if m["source"] == "stated" and len([x for x in strengths if x["source"] == "resume_fit"]) < 4:
                strengths.append({"label": m["skill"], "kind": "objective", "source": "resume_fit", "evidence": "Stated on your resume"})
    else:
        comps["resume_fit"] = _component("resume_fit", "missing", None, "No analysed resume was chosen.")

    # ---- technical knowledge (objective)
    a = i.assessment
    if a is not None:
        r = assessments.result(a)
        if r["mcq_total"] == 0:
            comps["technical_knowledge"] = _component("technical_knowledge", "missing", None, "This assessment had no multiple-choice questions to score.", sources=[str(a.id)])
        else:
            comps["technical_knowledge"] = _component(
                "technical_knowledge", "available", round(r["mcq_correct"] / r["mcq_total"] * 100), detail={"correct": r["mcq_correct"], "total": r["mcq_total"], "unanswered": r["mcq_unanswered"], "by_topic": r["by_topic"], "short_answers_saved_not_scored": r["short_answered"]},
                reason=f"{r['mcq_correct']} of {r['mcq_total']} multiple-choice questions correct.", sources=[str(a.id)], low_evidence=r["mcq_total"] < LOW_EVIDENCE_MCQ,
            )
            for t in r["by_topic"]:
                ratio = t["correct"] / t["total"]
                if t["total"] >= 2 and ratio < 0.5:
                    _gap(gaps, t["topic"], "high" if ratio < 0.34 else "medium", "objective", "assessment", f"{t['correct']} of {t['total']} correct")
                elif t["total"] == 1 and t["correct"] == 0:
                    _gap(gaps, t["topic"], "low", "objective", "assessment", "1 question, answered wrongly")
                elif t["total"] >= 2 and ratio >= 0.8:
                    strengths.append({"label": t["topic"], "kind": "objective", "source": "assessment", "evidence": f"{t['correct']} of {t['total']} correct"})
            by_q = {x.question_id: x for x in a.answers}
            for q in a.questions:
                if q.type == "mcq" and not (by_q.get(q.id) and by_q[q.id].is_correct) and len(practice) < 5:
                    practice.append({"type": "question", "prompt": q.prompt, "topic": q.topic, "label": "ai_generated_practice"})
            if r["short_total"]:
                notes.append("Short-answer questions are saved but not scored in this version, so they do not affect any number here.")
    else:
        comps["technical_knowledge"] = _component("technical_knowledge", "missing", None, "No assessment was included.")

    # ---- coding correctness (objective, only from real execution)
    cs = i.coding
    if cs is not None:
        passed = total = 0
        executed_all, any_submit, unsubmitted = True, False, []
        per_problem = []
        for slug in cs.problem_slugs:
            p = db.scalars(select(CodingProblem).where(CodingProblem.slug == slug)).first()
            last = coding._last_submit(cs, slug)
            title = p.title if p else slug
            n = last.total_count if last else (len(p.visible_tests) + len(p.hidden_tests) if p else 0)
            total += n
            if last is None:
                unsubmitted.append(title)
                per_problem.append({"slug": slug, "title": title, "submitted": False, "passed": 0, "total": n})
                continue
            any_submit = True
            if not last.executed:
                executed_all = False
            else:
                passed += last.passed_count or 0
            per_problem.append({"slug": slug, "title": title, "submitted": True, "executed": last.executed, "passed": last.passed_count if last.executed else None, "total": n})
        src = [str(cs.id)]
        if not any_submit:
            comps["coding_correctness"] = _component("coding_correctness", "missing", None, "No code was submitted in this session.", {"problems": per_problem}, src)
        elif not executed_all:
            comps["coding_correctness"] = _component(
                "coding_correctness", "not_run", None, "The code runner did not execute your code, so there is no correctness score. Nothing was guessed.", {"problems": per_problem}, src,
            )
        else:
            comps["coding_correctness"] = _component(
                "coding_correctness", "available", round(passed / total * 100) if total else 0, f"{passed} of {total} tests passed across {len(cs.problem_slugs)} problem(s).",
                {"passed": passed, "total": total, "problems": per_problem, "unsubmitted": unsubmitted}, src, low_evidence=len(cs.problem_slugs) < 2,
            )
            if unsubmitted:
                notes.append("Problems not submitted counted as 0 tests passed: " + ", ".join(unsubmitted) + ".")
            for pp in per_problem:
                p = db.scalars(select(CodingProblem).where(CodingProblem.slug == pp["slug"])).first()
                topic = (p.topics[0] if p and p.topics else pp["title"])
                if pp["total"] and pp["passed"] == pp["total"]:
                    strengths.append({"label": pp["title"], "kind": "objective", "source": "coding", "evidence": f"All {pp['total']} tests passed"})
                else:
                    ratio = (pp["passed"] or 0) / pp["total"] if pp["total"] else 0
                    _gap(gaps, topic, "high" if ratio < 0.5 else "medium", "objective", "coding", f"{pp['title']}: {pp['passed'] or 0} of {pp['total']} tests passed")
                    if len([x for x in practice if x["type"] == "coding"]) < 3:
                        practice.append({"type": "coding", "title": pp["title"], "slug": pp["slug"], "label": "ai_generated_practice"})
    else:
        comps["coding_correctness"] = _component("coding_correctness", "missing", None, "No coding session was included.")

    # ---- interview (subjective)
    iv = i.interview
    ev = iv.evaluation if iv is not None else None
    if ev:
        crit = {c["key"]: c for c in ev["criteria"]}
        limited = ev.get("evidence_level") == "limited"
        src = [str(iv.id)]
        det = {"criteria": [{"key": c["key"], "name": c["name"], "score": c["score"], "max": c["max"], "low_evidence": c["low_evidence"]} for c in ev["criteria"]], "answers_scored": ev["answers_scored"], "rubric_version": ev["rubric_version"]}
        comps["interview_performance"] = _component("interview_performance", "available", ev["indicator"], "Average of the four interview criteria; AI judgement of the text of your answers.", det, src, limited)
        r = crit.get("reasoning")
        comps["problem_solving"] = _component("problem_solving", "available", round(r["score"] / r["max"] * 100), "The interview reasoning criterion.", {"score": r["score"], "max": r["max"]}, src, limited or r["low_evidence"]) if r else _component("problem_solving", "missing", None, "The evaluation has no reasoning criterion.")
        cl, sp = crit.get("clarity"), crit.get("specificity")
        if cl and sp:
            comps["communication"] = _component("communication", "available", round((cl["score"] / cl["max"] + sp["score"] / sp["max"]) / 2 * 100), "Average of the clarity and specificity criteria, from text only.", {"clarity": cl["score"], "specificity": sp["score"]}, src, limited or cl["low_evidence"] or sp["low_evidence"])
        else:
            comps["communication"] = _component("communication", "missing", None, "The evaluation lacks clarity or specificity criteria.")
        for c in ev["criteria"]:
            if c["score"] <= 1 and not c["low_evidence"]:
                _gap(gaps, c["name"], "high" if c["score"] == 0 else "medium", "subjective", "interview", f"Scored {c['score']} of {c['max']} by the AI interview evaluation")
            elif c["score"] >= 3 and not c["low_evidence"]:
                strengths.append({"label": c["name"], "kind": "subjective", "source": "interview", "evidence": f"Scored {c['score']} of {c['max']} by the AI interview evaluation"})
        if limited:
            notes.append("The interview rested on fewer than three answers, so its scores are limited evidence.")
    else:
        why = "No interview was included." if iv is None else "This interview has no feedback yet."
        for k in ("interview_performance", "problem_solving", "communication"):
            comps[k] = _component(k, "missing", None, why)
    comps["complexity_analysis"] = _component("complexity_analysis", "not_scored", None, BY_KEY["complexity_analysis"]["how"])

    ordered = [comps[k] for k in BY_KEY]
    # ---- overall: only components that exist and carry weight
    inc = [c for c in ordered if c["status"] == "available" and c["weight"] > 0]
    weight = sum(c["weight"] for c in inc)
    if inc:
        value = round(sum(c["weight"] * c["value"] for c in inc) / weight)
        subj = round(sum(c["weight"] for c in inc if c["kind"] == "subjective") / weight * 100)
        note = f"Based on {len(inc)} of 3 scored components; the rest are missing (see below)." if len(inc) < 3 else "Based on all three scored components."
        overall = {"value": value, "included": [c["key"] for c in inc], "subjective_share": subj, "how": OVERALL_HOW, "note": note, "limited": len(inc) < 2 or any(c["low_evidence"] for c in inc)}
    else:
        overall = {"value": None, "included": [], "subjective_share": 0, "how": OVERALL_HOW, "note": "No scored component is available yet, so there is no overall indicator.", "limited": True}
    overall["missing"] = [{"key": c["key"], "name": c["name"], "status": c["status"], "reason": c["reason"]} for c in ordered if c["weight"] > 0 and c["status"] != "available"]

    gap_list = sorted(gaps.values(), key=lambda g: (SEVERITY[g["severity"]], 0 if g["kind"] == "objective" else 1, g["label"].lower()))[:8]
    return {"components": ordered, "overall": overall, "gaps": gap_list, "strengths": strengths[:8], "practice_questions": practice, "notes": notes}
