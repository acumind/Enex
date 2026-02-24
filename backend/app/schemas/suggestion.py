"""Suggestion request/response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class SuggestionCreate(BaseModel):
    url: str = Field(..., min_length=1, max_length=1000)
    note: str | None = Field(None, max_length=2000)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class SuggestionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    url: str
    note: str | None
    submitted_by: uuid.UUID
    status: str
    promoted_to: uuid.UUID | None
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime


class SuggestionDismiss(BaseModel):
    reason: str | None = Field(None, max_length=500)


class BulkExtractRequest(BaseModel):
    urls: list[str] = Field(..., min_length=1, max_length=20)

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        for url in v:
            if not url.startswith(("http://", "https://")):
                raise ValueError(f"Invalid URL: {url}")
        return v


class BulkExtractResponse(BaseModel):
    job_id: str
    total: int
    message: str
