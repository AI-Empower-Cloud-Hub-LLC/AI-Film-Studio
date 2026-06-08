"""
Authentication endpoints — register, login, refresh, profile,
email verification, password reset.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_token_pair,
    decode_token,
    TokenPair,
)
from app.services.email_service import (
    create_verification_token,
    create_password_reset_token,
    decode_verification_token,
    decode_reset_token,
    send_verification_email,
    send_password_reset_email,
)
from app.services.sanitizer import sanitize_text
from app.api.deps import get_current_user

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)
    full_name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class VerifyEmailRequest(BaseModel):
    token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    is_active: bool
    is_admin: bool
    email_verified: bool
    avatar_url: str | None
    created_at: str


class AuthResponse(BaseModel):
    user: UserResponse
    tokens: TokenPair


def _user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        is_active=user.is_active,
        is_admin=user.is_admin,
        email_verified=getattr(user, "email_verified", False),
        avatar_url=user.avatar_url,
        created_at=user.created_at.isoformat(),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
def register(request: Request, body: RegisterRequest, db: Session = Depends(get_db)):
    body.username = sanitize_text(body.username)
    body.full_name = sanitize_text(body.full_name)

    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        username=body.username,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    if settings.EMAIL_VERIFICATION_REQUIRED:
        token = create_verification_token(user.id, user.email)
        send_verification_email(user.email, token)

    tokens = create_token_pair(user.id, user.email)
    return AuthResponse(user=_user_response(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse)
@limiter.limit("20/minute")
def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

    if settings.EMAIL_VERIFICATION_REQUIRED and not getattr(user, "email_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Check your inbox for the verification link.",
        )

    tokens = create_token_pair(user.id, user.email)
    return AuthResponse(user=_user_response(user), tokens=tokens)


@router.post("/refresh", response_model=TokenPair)
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    token_data = decode_token(body.refresh_token)
    if token_data is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    user = db.query(User).filter(User.id == token_data.user_id, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return create_token_pair(user.id, user.email)


@router.post("/verify-email")
def verify_email(body: VerifyEmailRequest, db: Session = Depends(get_db)):
    """Verify user email with JWT token."""
    data = decode_verification_token(body.token)
    if not data:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.email_verified = True
    db.commit()
    return {"status": "verified", "email": user.email}


@router.post("/resend-verification")
@limiter.limit("5/minute")
def resend_verification(request: Request, body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Resend email verification link."""
    user = db.query(User).filter(User.email == body.email).first()
    if user and not getattr(user, "email_verified", False):
        token = create_verification_token(user.id, user.email)
        send_verification_email(user.email, token)
    return {"status": "ok", "message": "If the email exists, a verification link has been sent."}


@router.post("/forgot-password")
@limiter.limit("5/minute")
def forgot_password(request: Request, body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Send password reset link to email."""
    user = db.query(User).filter(User.email == body.email).first()
    if user:
        token = create_password_reset_token(user.id, user.email)
        send_password_reset_email(user.email, token)
    return {"status": "ok", "message": "If the email exists, a reset link has been sent."}


@router.post("/reset-password")
@limiter.limit("10/minute")
def reset_password(request: Request, body: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using token from email."""
    data = decode_reset_token(body.token)
    if not data:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"status": "ok", "message": "Password has been reset successfully."}


@router.post("/change-password")
def change_password(
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Change password for authenticated user."""
    if not verify_password(body.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.hashed_password = hash_password(body.new_password)
    db.commit()
    return {"status": "ok", "message": "Password changed successfully."}


@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return _user_response(current_user)


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None
    username: str | None = None


@router.put("/me", response_model=UserResponse)
def update_profile(
    body: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current user's profile."""
    if body.full_name is not None:
        current_user.full_name = sanitize_text(body.full_name)
    if body.avatar_url is not None:
        current_user.avatar_url = body.avatar_url
    if body.username is not None:
        existing = db.query(User).filter(User.username == body.username, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=409, detail="Username already taken")
        current_user.username = sanitize_text(body.username)
    db.commit()
    db.refresh(current_user)
    return _user_response(current_user)
