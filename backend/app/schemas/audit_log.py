"""Audit log response schema."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    actor_id: uuid.UUID
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    details: dict | None
    created_at: datetime
    actor_name: str | None = None
