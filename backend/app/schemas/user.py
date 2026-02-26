"""User request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import UserRole


class UserResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str | None
    phone: str | None
    name: str | None
    avatar_url: str | None
    role: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class UserDetailResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str | None
    phone: str | None
    name: str | None
    avatar_url: str | None
    role: str
    is_email_verified: bool
    is_phone_verified: bool
    auth_methods: list[str]
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None


class UserUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    avatar_url: str | None = Field(None, max_length=500)


class RoleChange(BaseModel):
    role: UserRole


class UserBan(BaseModel):
    ban_reason: str = Field(..., min_length=1, max_length=500)


class LoginEventResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    login_method: str
    ip_address: str | None
    user_agent: str | None
    created_at: datetime


class ActiveSessionsResponse(BaseModel):
    refresh_token_count: int
    login_events: list[LoginEventResponse]
