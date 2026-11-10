import logging
import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assessments import context
from app.companies import service as company_service
from app.core.config import get_settings
from app.core.db import utcnow
from app.core.errors import AppError, not_found
from app.core.ownership import get_owned_or_404
from app.core.rate_limit import interview_ai_limiter, interview_limiter
from app.interviews import evaluate as evaluator
from app.interviews import workflow
from app.interviews.schemas import AnswerIn, CreateInterviewIn, EventIn, EvidenceRef, InterviewOut, InterviewReviewOut, TurnOut
from app.llm.base import LLMError, LLMInvalidOutput, LLMNotConfigured, LLMRateLimited, LLMUnavailable
from app.llm.factory import get_llm_provider
from app.models.audit import record
from app.models.interview import InterviewSession, InterviewTurn
from app.models.resume import Resume
from app.models.user import User
from app.resumes import roles
from app.resumes.schemas import ParsedResume
from app.resumes.text import injection_signals

log = logging.getLogger("interviewpilot")
build_llm = get_llm_provider  # tests replace this hook
TRANSITIONS = {"active": {"completed", "interrupted"}, "interrupted": {"active", "completed"}, "completed": set()}
MAX_EVENTS = 50
NOTICE = (
    "Practice only. An AI writes the questions; they are not real questions from any company. Only the text of your answers is read: voice, face and "
    "appearance are not assessed. If you use speech input, some browsers send audio to their vendor for recognition. Scores are preparation indicators, not hiring predictions."
)


def transition(db: Session, s: InterviewSession, to: str) -> None:
    if to not in TRANSITIONS[s.status]:
        raise AppError(409, "invalid_state", f"This interview is {s.status} and can't become {to}.")
    s.status = to
    if to in ("completed", "interrupted"):
        s.ended_at = utcnow()


# ------------------------------------------------------------------ helpers
def _turns(db: Session, s: InterviewSession) -> list[InterviewTurn]:
    return list(db.scalars(select(InterviewTurn).where(InterviewTurn.session_id == s.id).order_by(InterviewTurn.position)).all())


def _add(db: Session, s: InterviewSession, speaker: str, kind: str, text: str, **kw) -> InterviewTurn:
    pos = (db.scalar(select(InterviewTurn.position).where(InterviewTurn.session_id == s.id).order_by(InterviewTurn.position.desc()).limit(1)) or 0) + 1
    t = InterviewTurn(session_id=s.id, user_id=s.user_id, position=pos, speaker=speaker, kind=kind, text=text, **kw)
    db.add(t)
    db.flush()
    return t


def purge_transcript(db: Session, s: InterviewSession) -> None:
    for t in _turns(db, s):
        db.delete(t)
    s.transcript_purged_at = utcnow()
    db.flush()


def refresh_state(db: Session, s: InterviewSession) -> None:
    """Lazy housekeeping on every read: idle sessions become interrupted; unkept transcripts are removed after the retention window."""
    cfg, now = get_settings(), utcnow()
    changed = False
    if s.status == "active" and now - s.last_activity_at > timedelta(minutes=cfg.interview_idle_minutes):
        transition(db, s, "interrupted")
        s.ended_at = s.last_activity_at
        changed = True
    if s.status != "active" and not s.save_transcript and s.transcript_purged_at is None and s.ended_at and now - s.ended_at > timedelta(hours=cfg.interview_purge_hours):
        purge_transcript(db, s)
        changed = True
    if changed:
        db.commit()


def _evidence_refs(s: InterviewSession, nums: list[int]) -> list[EvidenceRef]:
    by_n = {e["n"]: e for e in s.evidence}
    return [EvidenceRef(n=n, url=by_n[n]["url"], label=by_n[n]["label"]) for n in nums if n in by_n]


def _turn_out(s: InterviewSession, t: InterviewTurn) -> TurnOut:
    return TurnOut(
        id=t.id, position=t.position, speaker=t.speaker, kind=t.kind, text=t.text, topic=t.topic, source=t.source,
        informed_by=_evidence_refs(s, list(t.informed_by or [])), created_at=t.created_at,
    )


def out(db: Session, s: InterviewSession, with_turns: bool = True) -> InterviewOut:
    turns = _turns(db, s)
    asked = sum(1 for t in turns if t.kind == "question")
    answers = sum(1 for t in turns if t.kind == "answer")
    awaiting = s.status == "active" and bool(turns) and turns[-1].speaker == "interviewer" and turns[-1].kind in ("question", "follow_up")
    title = next((r["title"] for r in roles.list_roles() if r["slug"] == s.role_slug), s.role_slug)
    company = None
    if s.company_id:
        c = company_service.get_by_id(db, s.company_id)
        company = {"slug": c.slug, "name": c.name} if c else None
    cfg = get_settings()
    return InterviewOut(
        id=s.id, status=s.status, mode=s.mode, role={"slug": s.role_slug, "title": title}, company=company, input_mode=s.input_mode,
        question_target=s.question_target, questions_asked=asked, answers_given=answers, awaiting_answer=awaiting, notice=NOTICE,
        save_transcript=s.save_transcript, transcript_available=s.transcript_purged_at is None and bool(turns), transcript_purged_at=s.transcript_purged_at,
        evaluated=s.evaluation is not None, events=list(s.events or []), provider=s.provider, model=s.model, started_at=s.started_at,
        last_activity_at=s.last_activity_at, ended_at=s.ended_at, server_now=utcnow(), idle_minutes=cfg.interview_idle_minutes,
        turns=[_turn_out(s, t) for t in turns] if with_turns and s.transcript_purged_at is None else None,
    )


def _check_ai_budget(user: User) -> None:
    wait = interview_ai_limiter.retry_after(str(user.id), get_settings().interview_ai_calls_per_hour, 3600)
    if wait:
        raise AppError(429, "rate_limited", "Too many interview requests. Try again later.", headers={"Retry-After": str(wait)})


def _llm():
    try:
        return build_llm()
    except LLMNotConfigured:
        raise AppError(503, "llm_not_configured", "AI isn't set up on this server yet, so interviews can't run.") from None


def _generate(db: Session, user: User, s: InterviewSession, llm, *, allow_follow_up: bool, last_answer: str | None, last_kind: str | None) -> InterviewTurn | None:
    """Produce the interviewer's next turn (or the closing). Never raises for AI problems: a built-in question is used instead."""
    turns = _turns(db, s)
    asked_main = [t for t in turns if t.kind == "question"]
    slots = list(s.plan.get("slots", []))
    slot_i = len(asked_main)
    slots_left = slot_i < len(slots)
    cur_slot = (asked_main[-1].slot if asked_main else None)
    if allow_follow_up and cur_slot is not None:
        if sum(1 for t in turns if t.kind == "follow_up" and t.slot == cur_slot) >= workflow.MAX_FOLLOW_UPS:
            allow_follow_up = False
    if not slots_left:  # past the last main question: at most one follow-up, and only after a real answer
        allow_follow_up = allow_follow_up and not any(t.kind == "follow_up" and t.slot == cur_slot for t in turns)
    if len(turns) > 60:
        allow_follow_up = False
    target_slot = slots[slot_i] if slots_left else (slots[cur_slot] if cur_slot is not None and cur_slot < len(slots) else None)
    interviewer = [t.text for t in turns if t.speaker == "interviewer" and t.kind in ("question", "follow_up")]
    history = [{"speaker": t.speaker, "kind": t.kind, "text": t.text} for t in turns if t.kind not in ("opening", "closing")]
    interview_ai_limiter.add(str(user.id))
    d = workflow.next_turn(llm, s.plan["brief"], target_slot, list(s.evidence), history, interviewer, allow_follow_up, slots_left, last_answer)
    flags = [f"fallback:{d['llm_error']}"] if d.get("llm_error") else [f"rejected:{r}" for r in d.get("reasons", [])]
    if d["kind"] == "wrap_up":
        t = _add(db, s, "interviewer", "closing", workflow.closing_text(), source="system")
        transition(db, s, "completed")
        record(db, "interview_completed", user.id, interview_id=str(s.id))
        return t
    if d["kind"] == "question":
        t = _add(db, s, "interviewer", "question", d["message"], topic=d["topic"] or target_slot["topic"], slot=slot_i, source=d["source"], informed_by=d["informed_by"], flags=flags)
    else:
        t = _add(db, s, "interviewer", "follow_up", d["message"], topic=d["topic"] or (target_slot or {}).get("topic"), slot=cur_slot, source=d["source"], informed_by=d["informed_by"], flags=flags)
    return t


# ------------------------------------------------------------------ operations
def create(db: Session, user: User, data: CreateInterviewIn) -> InterviewSession:
    cfg = get_settings()
    if not data.consent:
        raise AppError(422, "consent_required", "Please agree to the privacy notice before starting. Your answers are sent to the AI provider and held to run the interview.")
    resume = get_owned_or_404(db, Resume, data.resume_id, user)
    if not resume.versions:
        raise AppError(409, "not_analyzed", "Analyse this resume first.")
    if not any(r["slug"] == data.role for r in roles.list_roles()):
        raise not_found("Role")
    company = company_service.get_selectable_by_slug(db, data.company) if data.company else None  # same visibility rule as the directory
    existing = db.scalars(select(InterviewSession).where(InterviewSession.user_id == user.id)).all()
    for e in existing:
        refresh_state(db, e)
        if e.status == "active":
            raise AppError(409, "interview_in_progress", "Finish or end your current interview first.", {"interview_id": str(e.id)})
    if len(existing) >= cfg.max_interviews_per_user:
        raise AppError(409, "interview_limit", f"You can keep up to {cfg.max_interviews_per_user} interviews. Delete an old one first.")
    llm = _llm()
    wait = interview_limiter.retry_after(str(user.id), cfg.interviews_per_hour, 3600)
    if wait:
        raise AppError(429, "rate_limited", "Too many interviews started. Try again later.", headers={"Retry-After": str(wait)})
    _check_ai_budget(user)
    version = resume.versions[-1]
    ctx = context.build(db, user.id, ParsedResume.model_validate(version.parsed_json), data.role, company)
    now = utcnow()
    s = InterviewSession(
        user_id=user.id, resume_id=resume.id, resume_version_id=version.id, company_id=company.id if company else None, role_slug=data.role,
        mode="company" if company else "general", status="active", input_mode=data.input_mode, question_target=data.question_count,
        plan={"brief": workflow.brief(ctx), "slots": workflow.make_plan(ctx, data.question_count)}, evidence=ctx.evidence,
        consent_at=now, save_transcript=user.profile.consent_voice_transcript if data.save_transcript is None else data.save_transcript,
        events=[], provider=llm.name, model=llm.model, started_at=now, last_activity_at=now,
    )
    db.add(s)
    db.flush()
    interview_limiter.add(str(user.id))
    record(db, "interview_started", user.id, interview_id=str(s.id))
    _add(db, s, "interviewer", "opening", workflow.opening_text(ctx.role["title"], ctx.company_name), source="system")
    _generate(db, user, s, llm, allow_follow_up=False, last_answer=None, last_kind=None)
    db.commit()
    return s


def answer(db: Session, user: User, s: InterviewSession, data: AnswerIn) -> InterviewSession:
    cfg = get_settings()
    if s.status != "active":
        raise AppError(409, "interview_ended", "This interview is no longer active." + (" Resume it to continue." if s.status == "interrupted" else ""))
    turns = _turns(db, s)
    if not turns or turns[-1].speaker != "interviewer" or turns[-1].kind not in ("question", "follow_up"):
        raise AppError(409, "not_your_turn", "There is no open question to answer.")
    if not data.skip and not data.text:
        raise AppError(422, "empty_answer", "Write or say something first, or skip the question.")
    if len(data.text) > cfg.interview_answer_max_chars:
        raise AppError(422, "answer_too_long", f"Keep answers under {cfg.interview_answer_max_chars} characters.")
    llm = _llm()
    _check_ai_budget(user)  # checked before anything is saved so the candidate can simply retry
    skipped = data.skip
    cand = _add(
        db, s, "candidate", "skipped" if skipped else "answer", "(skipped)" if skipped else data.text, slot=turns[-1].slot,
        source="" if skipped else data.source, flags=[] if skipped else [f"injection_signal:{x}" for x in injection_signals(data.text)],
    )
    s.last_activity_at = utcnow()
    allow = (not skipped) and len(data.text) >= 40  # one-line answers get a fresh question, not an interrogation
    _generate(db, user, s, llm, allow_follow_up=allow, last_answer=None if skipped else data.text, last_kind=cand.kind)
    db.commit()
    return s


def end(db: Session, user: User, s: InterviewSession) -> InterviewSession:
    if s.status == "completed":
        return s
    transition(db, s, "completed")
    record(db, "interview_ended", user.id, interview_id=str(s.id))
    db.commit()
    return s


def resume_session(db: Session, user: User, s: InterviewSession) -> InterviewSession:
    if s.status != "interrupted":
        raise AppError(409, "invalid_state", "Only an interrupted interview can be resumed.")
    if s.transcript_purged_at is not None:
        raise AppError(409, "transcript_gone", "The transcript of this interview was removed, so it can't continue.")
    for other in db.scalars(select(InterviewSession).where(InterviewSession.user_id == user.id, InterviewSession.id != s.id)).all():
        refresh_state(db, other)
        if other.status == "active":
            raise AppError(409, "interview_in_progress", "Finish or end your current interview first.", {"interview_id": str(other.id)})
    transition(db, s, "active")
    s.ended_at = None
    s.last_activity_at = utcnow()
    db.commit()
    return s


def event(db: Session, s: InterviewSession, data: EventIn) -> InterviewSession:
    if s.status != "active":
        raise AppError(409, "interview_ended", "This interview is no longer active.")
    ev = list(s.events or [])
    if len(ev) < MAX_EVENTS:
        ev.append({"kind": data.kind, "at": utcnow().isoformat()})
    s.events = ev
    if data.kind in ("mic_denied", "speech_unsupported", "speech_error"):
        s.input_mode = "text"  # the text fallback keeps the interview going
    s.last_activity_at = utcnow()
    db.commit()
    return s


def evaluate(db: Session, user: User, s: InterviewSession) -> InterviewReviewOut:
    if s.evaluation is not None:
        return InterviewReviewOut(interview=out(db, s), evaluation=s.evaluation)
    if s.status == "active":
        raise AppError(409, "end_first", "End the interview before asking for feedback.")
    if s.transcript_purged_at is not None:
        raise AppError(409, "transcript_gone", "The transcript was removed, so there is nothing left to evaluate.")
    turns = _turns(db, s)
    if not any(t.kind == "answer" for t in turns):
        raise AppError(409, "nothing_to_evaluate", "There are no answers to evaluate yet.")
    llm = _llm()
    _check_ai_budget(user)
    interview_ai_limiter.add(str(user.id))
    title = next((r["title"] for r in roles.list_roles() if r["slug"] == s.role_slug), s.role_slug)
    try:
        ev, signals = evaluator.evaluate(llm, [{"position": t.position, "speaker": t.speaker, "kind": t.kind, "text": t.text} for t in turns], title)
    except LLMRateLimited as e:
        raise AppError(429, "ai_rate_limited", "The AI provider is busy. Try again shortly.", headers={"Retry-After": str(e.retry_after or 30)}) from None
    except LLMUnavailable:
        raise AppError(503, "llm_unavailable", "The AI service is unavailable right now. Try again later.") from None
    except LLMInvalidOutput:
        raise AppError(502, "evaluation_failed", "The AI returned something we couldn't validate. Nothing was saved; try again.") from None
    except LLMError:
        raise AppError(503, "llm_unavailable", "The AI service is unavailable right now. Try again later.") from None
    ev.update({"provider": llm.name, "model": llm.model, "created_at": utcnow().isoformat(), "injection_signals": signals, "transcript_kept": s.save_transcript})
    s.evaluation = ev
    record(db, "interview_evaluated", user.id, interview_id=str(s.id))
    if not s.save_transcript:
        purge_transcript(db, s)  # the user did not ask to keep the transcript: scores and notes stay, the words go
    db.commit()
    from app.reports import auto as auto_report  # lazy: reports import this module

    auto_report.after_interview(db, s)
    return InterviewReviewOut(interview=out(db, s), evaluation=s.evaluation)


def review(db: Session, s: InterviewSession) -> InterviewReviewOut:
    return InterviewReviewOut(interview=out(db, s), evaluation=s.evaluation)


def delete_transcript(db: Session, user: User, s: InterviewSession) -> InterviewSession:
    if s.status == "active":
        raise AppError(409, "interview_active", "End the interview first.")
    if s.transcript_purged_at is None:
        purge_transcript(db, s)
        record(db, "interview_transcript_deleted", user.id, interview_id=str(s.id))
        db.commit()
    return s


def get_owned(db: Session, interview_id: uuid.UUID, user: User) -> InterviewSession:
    s = get_owned_or_404(db, InterviewSession, interview_id, user)
    refresh_state(db, s)
    return s
