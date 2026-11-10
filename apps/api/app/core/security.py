import hashlib
import secrets
from datetime import timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import get_settings
from app.core.db import utcnow

_hasher = PasswordHasher()  # Argon2id with the library's current recommended defaults
DUMMY_HASH = _hasher.hash("not-a-real-password")  # used to equalise timing for unknown emails
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(hashed: str, password: str) -> bool:
    try:
        return _hasher.verify(hashed, password)
    except (VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    return _hasher.check_needs_rehash(hashed)


def create_access_token(user_id: UUID, expires_delta: timedelta | None = None) -> str:
    s = get_settings()
    now = utcnow()
    exp = now + (expires_delta if expires_delta is not None else timedelta(minutes=s.access_token_minutes))
    return jwt.encode({"sub": str(user_id), "typ": "access", "iat": now, "exp": exp}, s.secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str) -> UUID | None:
    try:
        data = jwt.decode(token, get_settings().secret_key, algorithms=[ALGORITHM], options={"require": ["exp", "sub"]})
        if data.get("typ") != "access":
            return None
        return UUID(data["sub"])
    except (jwt.PyJWTError, ValueError):
        return None


def new_opaque_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()
