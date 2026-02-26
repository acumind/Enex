"""Runtime configuration request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class RuntimeConfigResponse(BaseModel):
    model_config = {"from_attributes": True}

    key: str
    value: str
    description: str | None
    updated_by: uuid.UUID | None
    updated_at: datetime


class RuntimeConfigUpdate(BaseModel):
    value: str = Field(min_length=1, max_length=1000)
