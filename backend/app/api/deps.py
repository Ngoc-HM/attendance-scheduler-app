"""Shared FastAPI dependencies: DB session, current user, role guards."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.i18n import t
from app.models.enums import Role, UserStatus
from app.models.user import User
from app.schemas.token import TokenPayload

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

DbSession = Annotated[Session, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


def get_current_user(db: DbSession, token: TokenDep) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=t("auth.invalid_credentials"),
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        token_data = TokenPayload(**payload)
        if token_data.sub is None:
            raise credentials_exc
    except (JWTError, ValidationError) as exc:
        raise credentials_exc from exc

    user = db.get(User, int(token_data.sub))
    if user is None:
        raise credentials_exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_active_user(current_user: CurrentUser) -> User:
    if current_user.status is not UserStatus.active:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=t("auth.inactive_user"))
    return current_user


ActiveUser = Annotated[User, Depends(get_current_active_user)]


def require_admin(current_user: ActiveUser) -> User:
    """Only role M is admin (spec §3)."""
    if current_user.role is not Role.M:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=t("auth.admin_required"))
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]


def ensure_self_or_admin(current_user: User, target_user_id: int) -> None:
    """Authorize access to ``target_user_id``'s data (§9.5 data minimization).

    A normal user may only touch their own records; admins may touch anyone's.
    Call from handlers that take a path/query user id.
    """
    if current_user.role is not Role.M and current_user.id != target_user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=t("auth.forbidden_other_user"))
