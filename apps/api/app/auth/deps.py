from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.auth.cookies import ACCESS
from app.core.db import get_db
from app.core.errors import AppError, not_authenticated
from app.core.security import decode_access_token
from app.models.user import User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(ACCESS)
    user_id = decode_access_token(token) if token else None
    if user_id is None:
        raise not_authenticated()
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise not_authenticated()
    return user


def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise AppError(403, "forbidden", "You don't have permission to do that.")
    return user
