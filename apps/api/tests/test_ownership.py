import uuid

from fastapi import Depends
from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.auth.deps import get_current_user
from app.core.db import Base, get_db, get_engine
from app.core.ownership import get_owned_or_404
from app.models.user import User


class Note(Base):
    """Test-only user-owned resource that stands in for resumes, reports, etc. in later phases."""

    __tablename__ = "test_notes"
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    text: Mapped[str] = mapped_column(String(100))


def _mount(app):
    @app.post("/api/v1/_notes")
    def create(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
        n = Note(user_id=user.id, text="private")
        db.add(n)
        db.commit()
        return {"id": str(n.id)}

    @app.get("/api/v1/_notes/{note_id}")
    def read(note_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
        return {"id": str(get_owned_or_404(db, Note, note_id, user).id)}


def test_user_cannot_read_another_users_resource_by_id(app, make_api):
    Note.__table__.create(bind=get_engine(), checkfirst=True)
    _mount(app)
    try:
        alice, bob, anon = make_api(), make_api(), make_api()
        alice.signup("alice@example.com")
        bob.signup("bob@example.com")
        note_id = alice.post("/_notes").json()["id"]
        assert alice.get(f"/_notes/{note_id}").status_code == 200
        r = bob.get(f"/_notes/{note_id}")
        assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"
        missing = bob.get(f"/_notes/{uuid.uuid4()}")
        assert missing.json() == r.json()  # a stranger's row is indistinguishable from a missing one
        assert anon.get(f"/_notes/{note_id}").status_code == 401
    finally:
        Note.__table__.drop(bind=get_engine(), checkfirst=True)
