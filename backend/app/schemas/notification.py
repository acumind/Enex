"""Notification response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel


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
