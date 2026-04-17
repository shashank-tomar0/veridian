"""Pydantic v2 schemas for authentication and user management."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class Permission(str, Enum):
    READ = "read"
    ANALYZE = "analyze"
    ADMIN = "admin"


class TokenRequest(BaseModel):
    """Login / token request."""
    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    """JWT token pair."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(3600, description="Access token TTL in seconds")


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserCreate(BaseModel):
    """New user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    organization: str | None = None
    permission: Permission = Permission.READ


class UserResponse(BaseModel):
    """Public user representation."""
    id: str
    email: str
    full_name: str
    organization: str | None = None
    permission: Permission
    created_at: datetime
    is_active: bool = True
