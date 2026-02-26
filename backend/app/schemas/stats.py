"""Platform-wide statistics schema."""

from decimal import Decimal

from pydantic import BaseModel, Field


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


class SystemHealthResponse(BaseModel):
    db_pool_size: int
    db_pool_checked_in: int
    db_pool_checked_out: int
    db_pool_overflow: int
    redis_latency_ms: float | None
    redis_memory: str | None
    redis_connected_clients: int | None
    celery_workers: int
    celery_active_tasks: int
    celery_reserved_tasks: int


class RecentEvaluation(BaseModel):
    prediction_id: str
    stock_symbol: str
    predictor_name: str
    outcome_status: str
    deviation_pct: float | None
    evaluated_at: str


class EvalDashboardResponse(BaseModel):
    total_evaluated: int
    total_pending: int
    hits: int
    misses: int
    partial_hits: int
    accuracy_pct: float | None
    avg_deviation_pct: float | None
    recent_evaluations: list[RecentEvaluation]
    evaluations_today: int
    evaluations_this_week: int


class AdminAlert(BaseModel):
    level: str = Field(description="warning or critical")
    category: str = Field(description="health, queue, or evaluation")
    message: str


class AdminAlertsResponse(BaseModel):
    alerts: list[AdminAlert]
    checked_at: str
