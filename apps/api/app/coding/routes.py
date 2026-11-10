import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.coding import focus, service
from app.coding.runner_client import get_runner
from app.coding.schemas import CodeIn, CreateSessionIn, DraftIn, ProblemPublic, ProblemSummary, ReviewOut, RunnerStatus, SessionOut, SessionSummary, SubmissionOut
from app.core.db import get_db
from app.core.errors import not_found
from app.core.ownership import get_owned_or_404
from app.models.coding import CodingSession, CodingSubmission
from app.models.user import User

router = APIRouter(prefix="/coding", tags=["coding"], dependencies=[Depends(get_current_user)])


def runner_dep():
    return get_runner()


def _session(db: Session, session_id: uuid.UUID, user: User) -> CodingSession:
    s = get_owned_or_404(db, CodingSession, session_id, user)
    service.refresh_state(db, s)
    return s


@router.get("/runner", response_model=RunnerStatus)
def runner_status(runner=Depends(runner_dep)):
    return runner.status()


@router.get("/companies")
def companies():
    """Software houses whose practice focus can shape a coding session. Focus is the project's own rough note, not verified company data."""
    return {"companies": focus.company_profiles(), "disclaimer": focus.DISCLAIMER}


@router.get("/companies/{slug}/set")
def company_set(slug: str, role: str | None = None, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """The company's fixed 25-problem practice set (10 easy, 10 medium, 5 hard) and which of them you have already solved."""
    return service.company_set_view(db, user, slug, role)


@router.get("/problems", response_model=list[ProblemSummary])
def problems(
    role: str | None = Query(default=None, max_length=80),
    difficulty: str | None = Query(default=None, max_length=8),
    topic: str | None = Query(default=None, max_length=60),
    db: Session = Depends(get_db),
):
    return [service.summary(p) for p in service.list_problems(db, role, difficulty, topic)]


@router.get("/problems/{slug}", response_model=ProblemPublic)
def problem(slug: str, db: Session = Depends(get_db)):
    return service.public(service.get_problem(db, slug))


@router.post("/sessions", response_model=SessionOut, status_code=201)
def create_session(body: CreateSessionIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = service.create_session(db, user, body)
    db.commit()
    return service.session_out(db, s, with_problems=True)


@router.get("/sessions", response_model=list[SessionSummary])
def list_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(CodingSession).where(CodingSession.user_id == user.id).order_by(CodingSession.created_at.desc())).all()
    for s in rows:
        service.refresh_state(db, s)
    return [service.session_summary(db, s) for s in rows]


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.session_out(db, _session(db, session_id, user), with_problems=True)


@router.put("/sessions/{session_id}/drafts/{slug}", response_model=SessionOut)
def save_draft(session_id: uuid.UUID, slug: str, body: DraftIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = _session(db, session_id, user)
    service.save_draft(db, s, slug, body.code)
    return service.session_out(db, s)


@router.post("/sessions/{session_id}/run", response_model=SubmissionOut)
def run_code(session_id: uuid.UUID, body: CodeIn, db: Session = Depends(get_db), user: User = Depends(get_current_user), runner=Depends(runner_dep)):
    s = _session(db, session_id, user)
    return service.sub_out(service.execute(db, s, user, runner, body.problem, body.code, "run"))


@router.post("/sessions/{session_id}/submit", response_model=SubmissionOut)
def submit_code(session_id: uuid.UUID, body: CodeIn, db: Session = Depends(get_db), user: User = Depends(get_current_user), runner=Depends(runner_dep)):
    s = _session(db, session_id, user)
    return service.sub_out(service.execute(db, s, user, runner, body.problem, body.code, "submit"))


@router.post("/sessions/{session_id}/finish", response_model=ReviewOut)
def finish_session(session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = _session(db, session_id, user)
    service.finish(db, s)
    return service.review(db, s)


@router.get("/sessions/{session_id}/review", response_model=ReviewOut)
def review_session(session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.review(db, _session(db, session_id, user))


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(session_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = _session(db, session_id, user)
    db.delete(s)
    db.commit()
    return Response(status_code=204)


@router.post("/submissions/{submission_id}/feedback", response_model=dict)
def submission_feedback(submission_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    sub = get_owned_or_404(db, CodingSubmission, submission_id, user)
    s = db.get(CodingSession, sub.session_id)
    if s is None:
        raise not_found()
    service.refresh_state(db, s)
    return service.feedback(db, user, sub, s)
