"""Platform-wide statistics schema."""

from decimal import Decimal

from pydantic import BaseModel


class PlatformStatsResponse(BaseModel):
    total_predictions: int
    total_predictors: int
    total_stocks: int
    avg_accuracy_pct: Decimal | None
    total_evaluated: int


class AdminStatsResponse(BaseModel):
    pending_predictions: int
    pending_suggestions: int
    total_users: int
    total_predictors: int
    total_stocks: int
    predictions_today: int
    predictions_this_week: int


class JobStatusResponse(BaseModel):
    task_id: str
    task_name: str
    status: str
    result: dict | None = None
    date_done: str | None = None
    traceback: str | None = None
