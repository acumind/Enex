"""Prediction request/response schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ExtractionMethod, PredictionStatus, SourceType


class PredictionCreate(BaseModel):
    predictor_id: uuid.UUID
    stock_id: uuid.UUID
    target_price: Decimal = Field(..., gt=0)
    price_at_prediction: Decimal = Field(..., gt=0)
    prediction_date: date
    target_date: date | None = None
    source_url: str = Field(..., min_length=1, max_length=1000)
    source_type: SourceType
    raw_quote: str | None = None
    extraction_method: ExtractionMethod = ExtractionMethod.manual
    ai_confidence: Decimal | None = None


class PredictionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    predictor_id: uuid.UUID
    stock_id: uuid.UUID
    target_price: Decimal
    price_at_prediction: Decimal
    prediction_date: date
    target_date: date | None
    default_eval_date: date
    source_url: str
    source_type: str
    source_archive_url: str | None
    raw_quote: str | None
    submitted_by: uuid.UUID | None
    extraction_method: str
    ai_confidence: Decimal | None
    status: str
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    upside_pct: Decimal | None = None

    # Optional enrichment fields (populated by enriched queries)
    stock_symbol: str | None = None
    stock_name: str | None = None
    predictor_name: str | None = None
    predictor_slug: str | None = None


class PredictionUpdate(BaseModel):
    target_price: Decimal | None = Field(None, gt=0)
    price_at_prediction: Decimal | None = Field(None, gt=0)
    prediction_date: date | None = None
    target_date: date | None = None
    source_url: str | None = Field(None, min_length=1, max_length=1000)
    source_type: SourceType | None = None
    raw_quote: str | None = None


class PredictionApprove(BaseModel):
    pass


class PredictionReject(BaseModel):
    reason: str | None = Field(None, max_length=500)


class ReviewQueueParams(BaseModel):
    status: PredictionStatus = PredictionStatus.pending_review
    cursor: datetime | None = None
    limit: int = Field(default=20, ge=1, le=100)


class BulkStatusChangeRequest(BaseModel):
    prediction_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)


class BulkStatusChangeResponse(BaseModel):
    updated: int
    failed: int
    errors: list[str]
