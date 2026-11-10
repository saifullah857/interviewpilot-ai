import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.assessments import service
from app.assessments.schemas import AnswersIn, AssessmentOut, CreateAssessmentIn, ReviewOut
from app.auth.deps import get_current_user
from app.core.config import get_settings
from app.core.db import get_db
from app.core.errors import AppError
from app.core.ownership import get_owned_or_404
from app.core.rate_limit import assessment_limiter
from app.models.assessment import Assessment
from app.models.user import User

router = APIRouter(prefix="/assessments", tags=["assessments"], dependencies=[Depends(get_current_user)])


def _owned(db: Session, assessment_id: uuid.UUID, user: User) -> Assessment:
    a = get_owned_or_404(db, Assessment, assessment_id, user)
    service.refresh_state(db, a)
    return a


@router.post("", response_model=AssessmentOut, status_code=202)
def create_assessment(body: CreateAssessmentIn, background: BackgroundTasks, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    s = get_settings()
    wait = assessment_limiter.retry_after(str(user.id), s.assessments_per_hour, 3600)
    if wait:
        raise AppError(429, "rate_limited", "Too many assessments. Try again later.", headers={"Retry-After": str(wait)})
    a = service.create(db, user, body)
    assessment_limiter.add(str(user.id))
    db.commit()
    background.add_task(service.execute_generation, a.id)
    return service.out(a)


@router.get("", response_model=list[AssessmentOut])
def list_assessments(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.scalars(select(Assessment).where(Assessment.user_id == user.id).order_by(Assessment.created_at.desc())).all()
    for a in rows:
        service.refresh_state(db, a)
    return [service.out(a) for a in rows]


@router.get("/{assessment_id}", response_model=AssessmentOut)
def get_assessment(assessment_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.out(_owned(db, assessment_id, user), with_questions=True)


@router.post("/{assessment_id}/start", response_model=AssessmentOut)
def start_assessment(assessment_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = _owned(db, assessment_id, user)
    service.start(db, a)
    return service.out(a, with_questions=True)


@router.put("/{assessment_id}/answers", response_model=AssessmentOut)
def save_answers(assessment_id: uuid.UUID, body: AnswersIn, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = _owned(db, assessment_id, user)
    if a.status == "submitted" and a.auto_submitted:
        raise AppError(409, "time_expired", "Time ran out and the assessment was submitted automatically.")
    service.save_answers(db, a, body)
    return service.out(a, with_questions=True)


@router.post("/{assessment_id}/submit", response_model=ReviewOut)
def submit_assessment(assessment_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = _owned(db, assessment_id, user)
    service.submit(db, a)
    return service.review(a)


@router.get("/{assessment_id}/review", response_model=ReviewOut)
def review_assessment(assessment_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return service.review(_owned(db, assessment_id, user))


@router.delete("/{assessment_id}", status_code=204)
def delete_assessment(assessment_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    a = _owned(db, assessment_id, user)
    db.delete(a)
    db.commit()
    return Response(status_code=204)
