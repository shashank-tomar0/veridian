"""Authentication router — login, register, refresh."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.auth.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from backend.deps import get_db
from backend.models.user import User
from backend.schemas.auth import (
    RefreshTokenRequest,
    TokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/v1/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(body: UserCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user account."""
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        id=str(uuid.uuid4()),
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        organization=body.organization,
        permission=body.permission.value,
        created_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info("auth.register", user_id=user.id, email=user.email)

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        organization=user.organization,
        permission=body.permission,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: TokenRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and return JWT token pair."""
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    access = create_access_token(user.id, user.permission)
    refresh = create_refresh_token(user.id)

    logger.info("auth.login", user_id=user.id)

    return TokenResponse(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Exchange a refresh token for a new access + refresh token pair."""
    payload = decode_token(body.refresh_token)
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=400, detail="Not a refresh token")

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    access = create_access_token(user.id, user.permission)
    refresh = create_refresh_token(user.id)

    return TokenResponse(access_token=access, refresh_token=refresh)
