import logging
import math
import random
import uuid
from collections import defaultdict
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assessments import bank, context, workflow
from app.assessments.schemas import (
    SCHEMA_VERSION,
    AnswersIn,
    AssessmentOut,
    CreateAssessmentIn,
    EvidenceRef,
    OptionOut,
    QuestionOut,
    ReviewOut,
    ReviewQuestion,
    SavedAnswer,
)
from app.companies import service as company_service
from app.core.config import get_settings
from app.core.db import get_engine, utcnow
from app.core.errors import AppError, not_found
from app.core.ownership import get_owned_or_404
from app.llm.base import LLMNotConfigured
from app.llm.factory import get_llm_provider
from app.models.assessment import Assessment, AssessmentAnswer, AssessmentQuestion
from app.models.audit import record
from app.models.resume import Resume, ResumeVersion
from app.models.user import User
from app.resumes import roles
from app.resumes.schemas import ParsedResume

log = logging.getLogger("interviewpilot")
STALE_GENERATION_MINUTES = 5
MIN_VALID_SHARE = 0.7
build_llm = get_llm_provider  # tests replace this hook

MESSAGES = {
    "ai_not_configured": "AI isn't set up on this server, so no assessment could be written.",
    "ai_unavailable": "The AI service was unavailable, so the assessment could not be written. Nothing was saved; try again later.",
    "insufficient_valid_questions": "Too few questions passed our quality checks, so none were kept. Try again, or choose another role.",
    "resume_missing": "The resume this assessment was based on no longer exists.",
    "timed_out": "Generation did not finish.",
    "internal_error": "Something went wrong on our side. Nothing was saved.",
}


def _fail(a: Assessment, code: str, summary: dict | None = None) -> None:
    a.status, a.error_code = "failed", code
    if summary is not None:
        a.summary = summary


def create(db: Session, user: User, data: CreateAssessmentIn) -> Assessment:
    s = get_settings()
    resume = get_owned_or_404(db, Resume, data.resume_id, user)
    if not resume.versions:
        raise AppError(409, "not_analyzed", "Analyse this resume first.")
    if not any(r["slug"] == data.role for r in roles.list_roles()):
        raise not_found("Role")
    company = company_service.get_selectable_by_slug(db, data.company) if data.company else None  # same visibility rule as the directory

    existing = db.scalars(select(Assessment).where(Assessment.user_id == user.id)).all()
    now = utcnow()
    for a in existing:
        if a.status == "generating":
            if now - a.created_at > timedelta(minutes=STALE_GENERATION_MINUTES):
                _fail(a, "timed_out")  # a crashed generation must not block the user forever
            else:
                raise AppError(409, "generation_in_progress", "An assessment is still being written. Wait for it to finish.")
    if len(existing) >= s.max_assessments_per_user:
        raise AppError(409, "assessment_limit", f"You can keep up to {s.max_assessments_per_user} assessments. Delete an old one first.")

    duration = data.duration_minutes or min(90, max(15, round(data.question_count * 1.5)))
    a = Assessment(
        user_id=user.id,
        resume_id=resume.id,
        resume_version_id=resume.versions[-1].id,
        role_slug=data.role,
        company_id=company.id if company else None,
        mode="general",
        status="generating",
        question_target=data.question_count,
        duration_minutes=duration,
        schema_version=SCHEMA_VERSION,
    )
    db.add(a)
    db.flush()
    record(db, "assessment_requested", user.id, assessment_id=str(a.id))
    return a


def execute_generation(assessment_id: uuid.UUID) -> None:
    """Background task: always leaves the assessment in a final state."""
    with Session(get_engine()) as db:
        a = db.get(Assessment, assessment_id)
        if a is None:
            return
        try:
            version = db.get(ResumeVersion, a.resume_version_id) if a.resume_version_id else None
            if version is None:
                _fail(a, "resume_missing")
                db.commit()
                return
            company = company_service.get_by_id(db, a.company_id) if a.company_id else None
            ctx = context.build(db, a.user_id, ParsedResume.model_validate(version.parsed_json), a.role_slug, company)
            try:
                llm = build_llm()
            except LLMNotConfigured:
                llm = None
            if llm is None:  # no AI configured: the built-in practice bank still lets the user practise
                state = {"accepted": [], "round": 0, "warnings": ["ai_not_configured"], "stats": {"generated": 0, "gen_calls": 0, "verify_calls": 0, "dropped": {}}, "error": "ai_not_configured"}
            else:
                state = workflow.run(ctx, a.question_target, llm)
            _persist(db, a, ctx, state, llm, company)
        except Exception:  # noqa: BLE001 - never leave an assessment stuck in "generating"
            log.exception("Assessment generation failed")
            db.rollback()
            a = db.get(Assessment, assessment_id)
            if a is not None:
                _fail(a, "internal_error")
                db.commit()


def _persist(db: Session, a: Assessment, ctx, state: dict, llm, company) -> None:
    stats = state["stats"]
    summary = {
        "target": a.question_target,
        "generated": stats["generated"],
        "gen_calls": stats["gen_calls"],
        "verify_calls": stats["verify_calls"],
        "dropped": dict(stats["dropped"]),
        "rounds": state["round"],
        "warnings": list(state["warnings"]),
        "focus_topics": ctx.focus_topics,
        "evidence_used": len(ctx.evidence),
        "missing_skills": ctx.missing[:10],
        "unchecked_kept": stats.get("unchecked_kept", 0),
    }
    accepted = list(state["accepted"])
    ai_count = len(accepted)
    if state.get("error") and not accepted:
        summary["ai_error"] = state["error"]
    # Top up from the built-in practice bank when the AI came up short, so practice is never blocked by a slow or unavailable AI.
    fallback = 0
    if len(accepted) < a.question_target:
        known = list(ctx.prior_prompts) + [x["q"].prompt for x in accepted]
        extra = bank.fill(a.role_slug, a.question_target - len(accepted), known, a.id.int)
        accepted.extend(extra)
        fallback = len(extra)
    summary["accepted"] = len(accepted)
    summary["fallback_used"] = fallback
    if len(accepted) < 5:
        _fail(a, "insufficient_valid_questions", summary)
        db.commit()
        return
    rng = random.Random(a.id.int)  # noqa: S311 - shuffling for fairness, not security; shuffle options so the key is not biased towards one position
    for pos, item in enumerate(accepted, start=1):
        q = item["q"]
        options, correct = list(q.options), q.correct_index
        if q.type == "mcq":
            order = list(range(4))
            rng.shuffle(order)
            options, correct = [q.options[i] for i in order], order.index(q.correct_index)
        refs = (
            [{"url": ctx.evidence[i - 1]["url"], "label": ctx.evidence[i - 1]["label"], "finding_id": ctx.evidence[i - 1]["finding_id"]} for i in q.informed_by]
            if item["category"] == "company_informed"
            else []
        )
        a.questions.append(
            AssessmentQuestion(
                position=pos,
                type=q.type,
                category=item["category"],
                prompt=q.prompt,
                options=options,
                correct_index=correct if q.type == "mcq" else None,
                reference_points=q.reference_points if q.type == "short_answer" else [],
                explanation=q.explanation,
                topic=q.topic,
                skills=q.skills,
                difficulty=q.difficulty,
                informed_by=refs,
                label="ai_generated_practice",
            )
        )
    a.question_count = len(accepted)
    if len(accepted) < a.question_target:
        a.duration_minutes = max(10, round(a.duration_minutes * len(accepted) / a.question_target))
    if ctx.evidence and company is not None and any(i["category"] == "company_informed" for i in accepted):
        a.mode = "company"
    else:
        a.mode = "general"
        if company is not None:
            a.notice = f"No approved evidence about {company.name} applies to this role yet, so this is general role preparation."
            a.company_id = None
    if llm is not None and ai_count > 0:
        a.provider, a.model = llm.name, llm.model
    else:
        a.provider, a.model = "builtin", "practice-bank"
    if fallback:
        why = "the AI service was unavailable" if ai_count == 0 else "the AI service was slow"
        extra_note = f"{fallback} question(s) come from the built-in practice bank because {why}; they are general and not tailored to your resume."
        a.notice = f"{a.notice} {extra_note}"[:300] if a.notice else extra_note[:300]
    a.summary, a.status = summary, "ready"
    record(db, "assessment_ready", a.user_id, assessment_id=str(a.id), questions=len(accepted))
    db.commit()


# ---------------- session lifecycle ----------------
def refresh_state(db: Session, a: Assessment) -> None:
    """Lazy housekeeping on every access: free a stuck generation, auto-submit an expired test."""
    now = utcnow()
    if a.status == "generating" and now - a.created_at > timedelta(minutes=STALE_GENERATION_MINUTES):
        _fail(a, "timed_out")
        db.commit()
    if a.status == "in_progress" and a.deadline_at and now > a.deadline_at + timedelta(seconds=get_settings().assessment_grace_seconds):
        submit(db, a, auto=True)


def start(db: Session, a: Assessment) -> None:
    if a.status == "in_progress":
        return
    if a.status != "ready":
        raise AppError(409, "not_startable", "This assessment cannot be started.")
    now = utcnow()
    a.started_at, a.deadline_at, a.status = now, now + timedelta(minutes=a.duration_minutes), "in_progress"
    record(db, "assessment_started", a.user_id, assessment_id=str(a.id))
    db.commit()


def save_answers(db: Session, a: Assessment, data: AnswersIn) -> None:
    if a.status != "in_progress":
        raise AppError(409, "not_in_progress", "This assessment is not in progress.")
    questions = {q.id: q for q in a.questions}
    existing = {x.question_id: x for x in a.answers}
    seen: set[uuid.UUID] = set()
    for item in data.answers:
        q = questions.get(item.question_id)
        if q is None:
            raise AppError(422, "unknown_question", "That question does not belong to this assessment.")
        if item.question_id in seen:
            raise AppError(422, "duplicate_answer", "Each question can appear once per request.")
        seen.add(item.question_id)
        if q.type == "mcq":
            if item.response_text:
                raise AppError(422, "wrong_answer_type", "Multiple-choice questions take a selected option.")
            if item.selected_index is not None and item.selected_index >= len(q.options):
                raise AppError(422, "bad_option", "That option does not exist.")
        elif item.selected_index is not None:
            raise AppError(422, "wrong_answer_type", "Short-answer questions take text.")
    for item in data.answers:
        row = existing.get(item.question_id)
        if row is None:
            row = AssessmentAnswer(assessment_id=a.id, question_id=item.question_id)
            a.answers.append(row)
            existing[item.question_id] = row
        row.selected_index = item.selected_index
        row.response_text = (item.response_text or "").strip() or None
        row.updated_at = utcnow()
    db.commit()


def submit(db: Session, a: Assessment, auto: bool = False) -> None:
    if a.status == "submitted":
        return
    if a.status != "in_progress":
        raise AppError(409, "not_in_progress", "This assessment is not in progress.")
    by_q = {x.question_id: x for x in a.answers}
    for q in a.questions:
        ans = by_q.get(q.id)
        if q.type == "mcq" and ans is not None:
            ans.is_correct = ans.selected_index is not None and ans.selected_index == q.correct_index  # objective grading only
    a.status, a.submitted_at, a.auto_submitted = "submitted", utcnow(), auto
    record(db, "assessment_submitted", a.user_id, assessment_id=str(a.id), auto=auto)
    db.commit()
    from app.reports import auto as auto_report  # lazy: reports import this module

    auto_report.after_assessment(db, a)


# ---------------- output ----------------
def _question_out(q: AssessmentQuestion) -> QuestionOut:
    return QuestionOut(
        id=q.id,
        position=q.position,
        type=q.type,
        category=q.category,
        prompt=q.prompt,
        options=[OptionOut(index=i, text=t) for i, t in enumerate(q.options or [])],
        difficulty=q.difficulty,
        topic=q.topic,
        label=q.label,
        informed_by=[EvidenceRef(url=r["url"], label=r["label"]) for r in (q.informed_by or [])],
        max_points=1 if q.type == "mcq" else 3,
    )


def out(a: Assessment, with_questions: bool = False) -> AssessmentOut:
    company = None
    if a.mode == "company" and a.company_id is not None:
        from app.models.company import Company

        # relationship-free lookup keeps this model decoupled; the company row is already cached in the session
        c = Session.object_session(a).get(Company, a.company_id)
        company = {"slug": c.slug, "name": c.name} if c else None
    role = next((r for r in roles.list_roles() if r["slug"] == a.role_slug), {"slug": a.role_slug, "title": a.role_slug})
    s = a.summary or {}
    qs = answers = None
    if with_questions and a.status == "in_progress":
        qs = [_question_out(q) for q in a.questions]
        answers = [SavedAnswer(question_id=x.question_id, selected_index=x.selected_index, response_text=x.response_text) for x in a.answers]
    return AssessmentOut(
        id=a.id,
        status=a.status,
        mode=a.mode,
        role=role,
        company=company,
        notice=a.notice,
        question_count=a.question_count,
        duration_minutes=a.duration_minutes,
        created_at=a.created_at,
        started_at=a.started_at,
        deadline_at=a.deadline_at,
        submitted_at=a.submitted_at,
        auto_submitted=a.auto_submitted,
        server_now=utcnow(),
        error_code=a.error_code,
        message=MESSAGES.get(a.error_code or ""),
        generation={
            "accepted": s.get("accepted", 0),
            "target": s.get("target", a.question_target),
            "dropped": sum((s.get("dropped") or {}).values()),
            "warnings": s.get("warnings", []),
        },
        score={k: result(a)[k] for k in ("mcq_correct", "mcq_total")} if a.status == "submitted" else None,
        questions=qs,
        answers=answers,
    )


def result(a: Assessment) -> dict:
    by_q = {x.question_id: x for x in a.answers}
    topics: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    mcq_total = mcq_correct = short_total = short_answered = 0
    for q in a.questions:
        ans = by_q.get(q.id)
        if q.type == "mcq":
            mcq_total += 1
            ok = bool(ans and ans.is_correct)
            mcq_correct += ok
            topics[q.topic][1] += 1
            topics[q.topic][0] += ok
        else:
            short_total += 1
            short_answered += 1 if ans and ans.response_text else 0
    return {
        "mcq_correct": mcq_correct,
        "mcq_total": mcq_total,
        "mcq_unanswered": sum(1 for q in a.questions if q.type == "mcq" and not (by_q.get(q.id) and by_q[q.id].selected_index is not None)),
        "short_answered": short_answered,
        "short_total": short_total,
        "evaluated": False,
        "by_topic": [{"topic": t, "correct": c, "total": n} for t, (c, n) in sorted(topics.items())],
        "note": "Multiple-choice answers are scored objectively. Short answers are saved but not scored in this version.",
    }


def review(a: Assessment) -> ReviewOut:
    if a.status != "submitted":
        raise AppError(409, "not_submitted", "Answers and explanations are shown after you submit.")
    by_q = {x.question_id: x for x in a.answers}
    items = []
    for q in a.questions:
        ans = by_q.get(q.id)
        items.append(
            ReviewQuestion(
                **_question_out(q).model_dump(),
                correct_index=q.correct_index,
                reference_points=list(q.reference_points or []),
                explanation=q.explanation,
                selected_index=ans.selected_index if ans else None,
                response_text=ans.response_text if ans else None,
                is_correct=ans.is_correct if ans else (False if q.type == "mcq" else None),
                needs_evaluation=q.type == "short_answer",
            )
        )
    return ReviewOut(assessment=out(a), questions=items, result=result(a))
