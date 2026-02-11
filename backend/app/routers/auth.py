from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select

from ..deps import get_session, get_current_user   # ← make sure get_current_user is here
from ..models import StaffUser
from ..security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    revoke_refresh_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ─── For JSON clients (mobile, frontend fetch/axios, etc.) ───
class LoginIn(BaseModel):
    email: EmailStr
    password: str


@router.post("/login", response_model=dict)
def login_json(payload: LoginIn, session: Session = Depends(get_session)):
    """
    Login with email + password (JSON body)
    Returns access + refresh tokens
    """
    user = session.exec(
        select(StaffUser).where(StaffUser.email == payload.email.lower())
    ).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    access_token = create_access_token(staff_user=user)
    refresh_token = create_refresh_token(session=session, staff_user=user)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# ─── For Swagger UI + OAuth2 Password Flow ───
@router.post("/token", response_model=dict)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    """
    OAuth2 compatible token endpoint (used by Swagger UI "Authorize" button)
    Use username = email
    """
    # Swagger sends "username" → we treat it as email
    login_input = LoginIn(
        email=form_data.username.strip().lower(),
        password=form_data.password,
    )

    # Reuse the same logic
    return login_json(payload=login_input, session=session)


# ─── Logout ───
class LogoutIn(BaseModel):
    refresh_token: str


@router.post("/logout", response_model=dict)
def logout(payload: LogoutIn, session: Session = Depends(get_session)):
    try:
        revoke_refresh_token(session, payload.refresh_token)
    except Exception:
        # We don't want to leak whether token was valid or not
        pass

    return {"ok": True}


# ─── Current user ───
@router.get("/me", response_model=dict)
def read_users_me(current_user: StaffUser = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role),
        "store_id": current_user.store_id,
    }
