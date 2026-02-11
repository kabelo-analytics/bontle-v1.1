from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlmodel import Session, select

from .config import settings
from .db import engine
from .models import StaffUser, RefreshToken


# ─── Password hashing ────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


# ─── JWT configuration ───────────────────────────────────────────────
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.jwt_access_minutes
REFRESH_TOKEN_EXPIRE_DAYS = settings.jwt_refresh_days

# This is what Swagger uses for the "Authorize" button
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/token",
    scheme_name="Bearer Authentication",
)


# ─── Session helper (local to avoid circular imports) ────────────────
def get_session():
    """Yield a database session."""
    with Session(engine) as session:
        yield session


def hash_password(password: str) -> str:
    """Hash a plaintext password using PBKDF2-SHA256."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(staff_user: StaffUser) -> str:
    """
    Create short-lived access token with user info.
    """
    expires = _utc_now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(staff_user.id),
        "role": str(staff_user.role),          # convert to string in case it's enum
        "store_id": staff_user.store_id,
        "type": "access",
        "exp": int(expires.timestamp()),
        "iat": int(_utc_now().timestamp()),
        "jti": secrets.token_hex(16),
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)


def create_refresh_token(*, session: Session, staff_user: StaffUser) -> str:
    """
    Create long-lived refresh token and store JTI in database.
    """
    expires = _utc_now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    jti = secrets.token_hex(16)

    payload = {
        "sub": str(staff_user.id),
        "type": "refresh",
        "exp": int(expires.timestamp()),
        "iat": int(_utc_now().timestamp()),
        "jti": jti,
    }

    token = jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)

    refresh_entry = RefreshToken(
        staff_user_id=staff_user.id,
        token_jti=jti,
        expires_at=expires,
    )
    session.add(refresh_entry)
    session.commit()

    return token


def decode_token(token: str) -> dict:
    """Decode and verify JWT token."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Annotated[Session, Depends(get_session)],
) -> StaffUser:
    """
    Validate access token and return current user.
    Raises 401 if anything is wrong.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise credentials_exception from exc

    user_id_str: str | None = payload.get("sub")
    token_type: str | None = payload.get("type")

    if user_id_str is None or token_type != "access":
        raise credentials_exception

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise credentials_exception

    user = session.get(StaffUser, user_id)
    if user is None:
        raise credentials_exception

    return user


def get_current_active_user(
    current_user: Annotated[StaffUser, Depends(get_current_user)],
) -> StaffUser:
    """Check that the user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def revoke_refresh_token(session: Session, token: str) -> None:
    """
    Mark a refresh token as revoked (if valid).
    Safe to call even with invalid/expired tokens.
    """
    try:
        payload = decode_token(token)
    except JWTError:
        return

    if payload.get("type") != "refresh":
        return

    jti = payload.get("jti")
    if not jti:
        return

    refresh_token = session.exec(
        select(RefreshToken).where(RefreshToken.token_jti == jti)
    ).first()

    if refresh_token:
        refresh_token.is_revoked = True
        session.add(refresh_token)
        session.commit()