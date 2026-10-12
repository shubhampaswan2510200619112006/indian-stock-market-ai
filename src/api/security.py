"""
API Security, Authentication & User Context Dependencies.

Provides JWT/Bearer/API-Key validation backed by AuthService, ensuring
strict multi-tenant isolation across all paper trading and execution workflows.
Includes rate limiting and origin protection.
"""

from __future__ import annotations

import os
import time
from collections import defaultdict
from typing import Dict, List, Optional

from fastapi import Depends, Header, HTTPException, Request, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.service import AuthService, UserAccount
from src.paper_trading.service import PaperTradingService

# Bearer security scheme (optional flag allows graceful custom error handling)
_bearer_scheme = HTTPBearer(auto_error=False)

# Cached per-user PaperTradingService instances
_user_services: Dict[str, PaperTradingService] = {}
_shared_default_service: Optional[PaperTradingService] = None


class SimpleRateLimiter:
    """Sliding-window in-memory IP rate limiter."""

    def __init__(self, requests_per_minute: int = 60, name: str = "default"):
        self.requests_per_minute = requests_per_minute
        self.name = name
        self.requests: Dict[str, List[float]] = defaultdict(list)

    async def __call__(self, request: Request):
        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()
        window_start = now - 60.0
        # Prune timestamps older than window
        self.requests[client_ip] = [t for t in self.requests[client_ip] if t > window_start]
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded on {self.name}. Maximum {self.requests_per_minute} requests per minute.",
                headers={"Retry-After": "60"},
            )
        self.requests[client_ip].append(now)

    def reset(self):
        """Clears recorded requests for test isolation or manual reset."""
        self.requests.clear()


auth_rate_limiter = SimpleRateLimiter(requests_per_minute=20, name="auth")
trading_rate_limiter = SimpleRateLimiter(requests_per_minute=60, name="trading")


def get_auth_service() -> AuthService:
    """Returns the singleton AuthService instance."""
    db_path = os.getenv("USERS_DB_PATH", "data/users.db")
    return AuthService(db_path=db_path)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    auth_svc: AuthService = Depends(get_auth_service),
) -> UserAccount:
    """
    Extracts and validates the authentication token from Authorization header or X-API-Key.
    Raises 401 Unauthorized if missing or invalid.
    """
    token: Optional[str] = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif x_api_key:
        token = x_api_key

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required: Provide a valid Bearer token in Authorization header or X-API-Key.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = auth_svc.verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(_bearer_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    auth_svc: AuthService = Depends(get_auth_service),
) -> Optional[UserAccount]:
    """
    Optional authentication for endpoints that support both public and user-scoped data.
    """
    token: Optional[str] = None
    if credentials and credentials.credentials:
        token = credentials.credentials
    elif x_api_key:
        token = x_api_key

    if not token:
        return None

    return auth_svc.verify_token(token)


def get_user_paper_service(user: UserAccount = Depends(get_current_user)) -> PaperTradingService:
    """
    Returns an isolated PaperTradingService instance dedicated strictly to the authenticated user.
    State is persisted in data/user_state/{user_id}.
    """
    global _user_services
    if user.id not in _user_services:
        user_state_dir = f"data/user_state/{user.id}"
        _user_services[user.id] = PaperTradingService(
            initial_capital=user.starting_capital,
            state_dir=user_state_dir,
            auto_restore=True,
            user_id=user.id,
        )
    return _user_services[user.id]


def get_optional_user_paper_service(
    user: Optional[UserAccount] = Depends(get_current_user_optional),
) -> PaperTradingService:
    """
    Returns the user's isolated PaperTradingService if authenticated,
    otherwise returns a global read-only instance for public health/status metrics.
    """
    global _shared_default_service
    if user:
        return get_user_paper_service(user)
    if _shared_default_service is None:
        _shared_default_service = PaperTradingService(state_dir="data/paper_state", auto_restore=True)
    return _shared_default_service
