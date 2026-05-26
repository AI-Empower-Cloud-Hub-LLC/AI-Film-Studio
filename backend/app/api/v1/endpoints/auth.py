"""
Authentication endpoints — register, login, refresh, profile.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.services.auth_service import (
    hash_password,
    verify_password,
    create_token_pair,
    decode_token,
    TokenPair,
)
from app.api.deps import get_current_user

router = APIRouter()


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


class UserResponse(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    is_active: bool
    is_admin: bool
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
        avatar_url=user.avatar_url,
        created_at=user.created_at.isoformat(),
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
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

    tokens = create_token_pair(user.id, user.email)
    return AuthResponse(user=_user_response(user), tokens=tokens)


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account deactivated")

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


@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return _user_response(current_user)


@router.put("/me", response_model=UserResponse)
def update_profile(
    full_name: str | None = None,
    avatar_url: str | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if full_name is not None:
        current_user.full_name = full_name
    if avatar_url is not None:
        current_user.avatar_url = avatar_url
    db.commit()
    db.refresh(current_user)
    return _user_response(current_user)
