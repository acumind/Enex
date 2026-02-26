"""Notification response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    user_id: uuid.UUID
    type: str
    title: str
    message: str | None
    data: dict[str, str]
    is_read: bool
    created_at: datetime


class UnreadCountResponse(BaseModel):
    count: int


class BroadcastRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    message: str = Field(min_length=1, max_length=2000)
    type: str = Field(default="system")
    role_filter: str | None = None


class BroadcastResponse(BaseModel):
    recipients: int
    message: str
