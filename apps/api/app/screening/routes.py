import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.core.db import get_db
from app.core.errors import AppError
from app.core.ownership import get_owned_or_404
from app.models.screening import ScreeningSession
from app.models.user import User
from app.screening import service
from app.screening.schemas import AnswerIn, CreateScreeningIn, ScreeningOut, ScreeningResult, ScreeningSummary

router = APIRouter(prefix="/screening", tags=["screening"], dependencies=[Depends(get_current_user)])


def _get(db: Session, sid: uuid.UUID, user: User) -> ScreeningSession:
    s = get_owned_or_404(db, ScreeningSession, sid, user)
    service.refresh(db, s)
    return s


@router.post("/sessions", status_code=201, response_model=ScreeningOut)
def create(body: CreateScreeningIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.out(db, service.create(db, user, body))


@router.get("/sessions", response_model=list[ScreeningSummary])
def list_sessions(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(ScreeningSession).where(ScreeningSession.user_id == user.id).order_by(ScreeningSession.created_at.desc()).limit(50)).all()
    for s in rows:
        service.refresh(db, s)
    return [service.summary(s) for s in rows]


@router.get("/sessions/{sid}", response_model=ScreeningOut)
def get_session(sid: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.out(db, _get(db, sid, user))


@router.put("/sessions/{sid}/answers", response_model=ScreeningOut)
def save_answer(sid: uuid.UUID, body: AnswerIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.answer(db, _get(db, sid, user), body)


@router.post("/sessions/{sid}/submit", response_model=ScreeningResult)
def submit(sid: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = service.submit(db, _get(db, sid, user))
    return service.result(db, s)


@router.get("/sessions/{sid}/review", response_model=ScreeningResult)
def review(sid: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = _get(db, sid, user)
    if s.status != "submitted":
        raise AppError(409, "not_finished", "Submit the test to see the answers.")
    return service.result(db, s)
