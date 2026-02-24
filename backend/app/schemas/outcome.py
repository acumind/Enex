"""Outcome, scorecard, and leaderboard response schemas."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class PredictionOutcomeResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    prediction_id: uuid.UUID
    outcome_status: str
    actual_price: Decimal | None
    highest_price: Decimal | None
    lowest_price: Decimal | None
    deviation_pct: Decimal | None
    evaluated_at: datetime | None
    evaluation_date: date | None
    created_at: datetime
    updated_at: datetime


class ScorecardResponse(BaseModel):
    model_config = {"from_attributes": True}

    predictor_id: uuid.UUID
    total_predictions: int
    hits: int
    misses: int
    partial_hits: int
    pending: int
    accuracy_pct: Decimal | None
    avg_deviation_pct: Decimal | None
    avg_upside_predicted: Decimal | None
    best_sector: str | None
    worst_sector: str | None
    sector_accuracy: dict[str, float]
    streak_current: int
    last_prediction_date: date | None
    last_updated: datetime


class LeaderboardEntry(BaseModel):
    predictor_id: uuid.UUID
    predictor_name: str
    predictor_slug: str
    predictor_type: str
    total_predictions: int
    hits: int
    misses: int
    partial_hits: int
    accuracy_pct: Decimal | None
    avg_deviation_pct: Decimal | None
    streak_current: int


class EvaluationTriggerResponse(BaseModel):
    message: str
    predictions_evaluated: int
    scorecards_updated: int
