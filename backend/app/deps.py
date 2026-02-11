from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
from sqlmodel import Session, select
from jose import JWTError

from .db import engine
from .models import StaffUser
from .security import decode_token


# ─── OAuth2 scheme ───────────────────────────────────────────────────
# This tells Swagger/OpenAPI where to send the login request
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",              # ← Changed from /auth/login
    scheme_name="Bearer Authentication",
)


def get_session():
    """Provide a database session (used as dependency)."""
    with Session(engine) as session:
        yield session


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> StaffUser:
    """
    Validate JWT access token and return the current active user.
    Raises 401 if token is invalid, expired, wrong type, or user not found/inactive.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        data = decode_token(token)
    except JWTError as exc:
        raise credentials_exception from exc

    if data.get("type") != "access":
        raise credentials_exception

    user_id_str = data.get("sub")
    if not user_id_str:
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = session.exec(select(StaffUser).where(StaffUser.id == user_id)).first()

    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )

    return user
