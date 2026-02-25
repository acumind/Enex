"""Platform-wide statistics schema."""

from decimal import Decimal

from pydantic import BaseModel


class PlatformStatsResponse(BaseModel):
    total_predictions: int
    total_predictors: int
    total_stocks: int
    avg_accuracy_pct: Decimal | None
    total_evaluated: int
