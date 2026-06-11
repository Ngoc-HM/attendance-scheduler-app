"""Password hashing and JWT helpers (spec §2 — lightweight auth)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import jwt

from app.core.config import settings

# bcrypt hashes only the first 72 bytes of input; truncate explicitly so long
# passwords don't raise (matches the historical passlib behaviour).
_BCRYPT_MAX_BYTES = 72


def _to_bcrypt_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        _to_bcrypt_bytes(plain_password), hashed_password.encode("utf-8")
    )


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(_to_bcrypt_bytes(password), bcrypt.gensalt()).decode("utf-8")


def create_access_token(
    subject: str | Any, expires_delta: timedelta | None = None
) -> str:
    """Create a signed JWT whose ``sub`` claim is the user id."""
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
