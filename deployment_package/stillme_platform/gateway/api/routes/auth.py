# StillMe Gateway - Authentication Routes
"""
Authentication endpoints
"""

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel

from core.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    verify_token,
)
from core.config import Settings

logger = logging.getLogger(__name__)

router = APIRouter()
settings = Settings()


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    """Authenticate user and return tokens"""
    try:
        # TODO: Implement actual authentication logic
        # For now, accept any username/password combination

        if not request.username or not request.password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        # Create tokens
        token_data = {
            "sub": request.username,
            "username": request.username,
            "email": f"{request.username}@stillme.ai",
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed"
        )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(request: RefreshRequest) -> LoginResponse:
    """Refresh access token using refresh token"""
    try:
        # Verify refresh token
        payload = verify_token(request.refresh_token)

        # Check if it's a refresh token
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type"
            )

        # Create new tokens
        token_data = {
            "sub": payload.get("sub"),
            "username": payload.get("username"),
            "email": payload.get("email"),
        }

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token refresh failed"
        )


@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, Any]:
    """Get current user information"""
    return {
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "email": current_user["email"],
        "permissions": current_user["permissions"],
    }


@router.post("/logout")
async def logout(
    current_user: Dict[str, Any] = Depends(get_current_user),
) -> Dict[str, str]:
    """Logout user (invalidate tokens)"""
    # TODO: Implement token blacklisting
    return {"message": "Logged out successfully"}


@router.get("/verify")
async def verify_token_endpoint(
    credentials: HTTPAuthorizationCredentials = Depends(get_current_user),
) -> Dict[str, Any]:
    """Verify token validity"""
    return {"valid": True, "message": "Token is valid"}
