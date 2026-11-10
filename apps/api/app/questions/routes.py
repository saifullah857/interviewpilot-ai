from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user, require_admin
from app.core.db import get_db
from app.models.audit import record
from app.models.user import User
from app.questions import service
from app.questions.schemas import AdminQuestionOut, QuestionOut, QuestionPatch, QuestionSpec, RevealOut

router = APIRouter(prefix="/questions", tags=["questions"])
admin = APIRouter(prefix="/admin/questions", tags=["admin-questions"])


@router.get("/stats")
def stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.stats(db)


@router.get("")
def list_questions(company: str | None = Query(default=None, max_length=80), role: str | None = Query(default=None, max_length=80), category: str | None = Query(default=None, max_length=40), difficulty: str | None = Query(default=None, pattern="^(easy|medium|hard)$"), kind: str | None = Query(default=None, pattern="^(technical|scenario|mcq|output)$"), source: str | None = Query(default=None, pattern="^(verified|reported|company_focused_practice)$"), q: str | None = Query(default=None, max_length=80), limit: int = Query(default=50, ge=1, le=100), offset: int = Query(default=0, ge=0), db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    total, rows = service.search(db, company, role, category, difficulty, kind, source, q, False, limit, offset)
    return {"total": total, "items": [service.public(r) for r in rows], "source_titles": service.SOURCE_TITLES}


@router.get("/{slug}", response_model=QuestionOut)
def get_question(slug: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.public(service.get(db, slug))


@router.post("/{slug}/reveal", response_model=RevealOut)
def reveal(slug: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """Study mode: shows the ideal answer. Assessments that score you never call this before you answer."""
    return service.reveal(service.get(db, slug))


def _admin_out(q) -> AdminQuestionOut:
    return AdminQuestionOut.model_validate({**{c: getattr(q, c) for c in QuestionSpec.model_fields}, "id": str(q.id)})


@admin.get("")
def admin_list(company: str | None = None, role: str | None = None, category: str | None = None, difficulty: str | None = None, kind: str | None = None, source: str | None = None, q: str | None = None, limit: int = Query(default=50, ge=1, le=200), offset: int = Query(default=0, ge=0), db: Session = Depends(get_db), _: User = Depends(require_admin)):
    total, rows = service.search(db, company, role, category, difficulty, kind, source, q, True, limit, offset)
    return {"total": total, "items": [_admin_out(r) for r in rows]}


@admin.post("", status_code=201, response_model=AdminQuestionOut)
def admin_create(body: QuestionSpec, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    q = service.create(db, body)
    record(db, "question_created", user.id, slug=q.slug)
    db.commit()
    return _admin_out(q)


@admin.patch("/{slug}", response_model=AdminQuestionOut)
def admin_update(slug: str, body: QuestionPatch, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    q = service.update(db, slug, body)
    record(db, "question_updated", user.id, slug=slug)
    db.commit()
    return _admin_out(q)


@admin.delete("/{slug}", status_code=204)
def admin_delete(slug: str, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    service.delete(db, slug)
    record(db, "question_deleted", user.id, slug=slug)
    db.commit()
    return Response(status_code=204)
