"""
Authentication & User Session API Routes.

Provides registration, login, token generation, and account profile endpoints.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.security import auth_rate_limiter, get_auth_service, get_current_user
from src.auth.service import AuthService, UserAccount

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=100)
    starting_capital: float = Field(1_000_000.0, ge=10_000.0, le=100_000_000.0)


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserAccount


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(auth_rate_limiter)],
)
async def register(request: RegisterRequest, auth_svc: AuthService = Depends(get_auth_service)):
    """Registers a new trader account and returns an authentication access token."""
    success, msg, user = auth_svc.register(
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        starting_capital=request.starting_capital,
    )
    if not success or not user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    token = auth_svc.create_token_for_user(user.id, description="register_token")
    return AuthResponse(access_token=token, token_type="bearer", user=user)


@router.post(
    "/login",
    response_model=AuthResponse,
    dependencies=[Depends(auth_rate_limiter)],
)
async def login(request: LoginRequest, auth_svc: AuthService = Depends(get_auth_service)):
    """Authenticates a trader with credentials and returns an access token."""
    success, msg, user, token = auth_svc.login_with_token(
        username_or_email=request.username_or_email,
        password=request.password,
    )
    if not success or not user or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthResponse(access_token=token, token_type="bearer", user=user)


@router.get("/me", response_model=UserAccount)
async def get_current_user_profile(user: UserAccount = Depends(get_current_user)):
    """Returns the authenticated trader's account details."""
    return user
