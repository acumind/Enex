"""Predictor request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import PredictorType


class PredictorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: PredictorType
    parent_id: uuid.UUID | None = None
    designation: str | None = Field(None, max_length=200)
    bio: str | None = None
    avatar_url: str | None = Field(None, max_length=500)
    website: str | None = Field(None, max_length=500)
    social_links: dict[str, str] = Field(default_factory=dict)
    sebi_reg_no: str | None = Field(None, max_length=50)


class PredictorUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    designation: str | None = Field(None, max_length=200)
    bio: str | None = None
    avatar_url: str | None = Field(None, max_length=500)
    website: str | None = Field(None, max_length=500)
    social_links: dict[str, str] | None = None
    sebi_reg_no: str | None = Field(None, max_length=50)
    is_verified: bool | None = None


class PredictorAdminUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    type: PredictorType | None = None
    description: str | None = None
    website: str | None = Field(None, max_length=500)
    is_active: bool | None = None


class PredictorResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    slug: str
    type: str
    parent_id: uuid.UUID | None
    designation: str | None
    bio: str | None
    avatar_url: str | None
    website: str | None
    social_links: dict[str, str]
    sebi_reg_no: str | None
    is_verified: bool
    created_at: datetime
    updated_at: datetime
