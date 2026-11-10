import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.core.db import get_db
from app.interviews import service
from app.interviews.schemas import AnswerIn, CreateInterviewIn, EventIn, InterviewOut, InterviewReviewOut
from app.models.interview import InterviewSession
from app.models.user import User

router = APIRouter(prefix="/interviews", tags=["interviews"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=InterviewOut, status_code=201)
def create_interview(body: CreateInterviewIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.out(db, service.create(db, user, body))


@router.get("", response_model=list[InterviewOut])
def list_interviews(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(InterviewSession).where(InterviewSession.user_id == user.id).order_by(InterviewSession.created_at.desc())).all()
    for s in rows:
        service.refresh_state(db, s)
    return [service.out(db, s, with_turns=False) for s in rows]


@router.get("/{interview_id}", response_model=InterviewOut)
def get_interview(interview_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.out(db, service.get_owned(db, interview_id, user))


@router.post("/{interview_id}/answer", response_model=InterviewOut)
def answer(interview_id: uuid.UUID, body: AnswerIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = service.get_owned(db, interview_id, user)
    return service.out(db, service.answer(db, user, s, body))


@router.post("/{interview_id}/event", response_model=InterviewOut)
def client_event(interview_id: uuid.UUID, body: EventIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.out(db, service.event(db, service.get_owned(db, interview_id, user), body))


@router.post("/{interview_id}/end", response_model=InterviewOut)
def end_interview(interview_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.out(db, service.end(db, user, service.get_owned(db, interview_id, user)))


@router.post("/{interview_id}/resume", response_model=InterviewOut)
def resume_interview(interview_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.out(db, service.resume_session(db, user, service.get_owned(db, interview_id, user)))


@router.post("/{interview_id}/evaluate", response_model=InterviewReviewOut)
def evaluate_interview(interview_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.evaluate(db, user, service.get_owned(db, interview_id, user))


@router.get("/{interview_id}/review", response_model=InterviewReviewOut)
def review_interview(interview_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.review(db, service.get_owned(db, interview_id, user))


@router.delete("/{interview_id}/transcript", response_model=InterviewOut)
def delete_transcript(interview_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.out(db, service.delete_transcript(db, user, service.get_owned(db, interview_id, user)))


@router.delete("/{interview_id}", status_code=204)
def delete_interview(interview_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = service.get_owned(db, interview_id, user)
    db.delete(s)
    db.commit()
    return Response(status_code=204)
