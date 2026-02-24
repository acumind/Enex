"""Shared schema primitives: pagination, enums, error response."""

from datetime import datetime
from enum import StrEnum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PredictorType(StrEnum):
    individual = "individual"
    brokerage = "brokerage"
    research_firm = "research_firm"
    media_house = "media_house"
    influencer = "influencer"


class PredictionStatus(StrEnum):
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    duplicate = "duplicate"


class SuggestionStatus(StrEnum):
    pending = "pending"
    promoted = "promoted"
    dismissed = "dismissed"


class ExtractionMethod(StrEnum):
    manual = "manual"
    ai_assisted = "ai_assisted"
    ai_auto = "ai_auto"


class UserRole(StrEnum):
    user = "user"
    moderator = "moderator"
    admin = "admin"


class SourceType(StrEnum):
    tv_interview = "tv_interview"
    news_article = "news_article"
    research_report = "research_report"
    social_media = "social_media"
    podcast = "podcast"
    blog = "blog"
    other = "other"


class PaginationParams(BaseModel):
    cursor: datetime | None = None
    limit: int = Field(default=20, ge=1, le=100)


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: datetime | None = None
    has_more: bool = False


class ErrorResponse(BaseModel):
    detail: str
