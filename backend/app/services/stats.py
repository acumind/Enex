"""Platform statistics aggregation service."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cached_response
from app.models.prediction import Prediction, PredictionOutcome
from app.models.scorecard import PredictorScorecard
from app.schemas.stats import PlatformStatsResponse


class StatsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @cached_response("platform_stats", ttl_seconds=300)
    async def get_platform_stats(self) -> PlatformStatsResponse:
        # Total approved predictions
        total_predictions = (
            await self.session.scalar(
                select(func.count()).select_from(Prediction).where(Prediction.status == "approved")
            )
            or 0
        )

        # Distinct predictors with ≥1 approved prediction
        total_predictors = (
            await self.session.scalar(
                select(func.count(func.distinct(Prediction.predictor_id))).where(Prediction.status == "approved")
            )
            or 0
        )

        # Distinct stocks with ≥1 approved prediction
        total_stocks = (
            await self.session.scalar(
                select(func.count(func.distinct(Prediction.stock_id))).where(Prediction.status == "approved")
            )
            or 0
        )

        # Average accuracy from scorecards with ≥10 predictions
        avg_accuracy_pct = await self.session.scalar(
            select(func.avg(PredictorScorecard.accuracy_pct)).where(PredictorScorecard.total_predictions >= 10)
        )

        # Total evaluated outcomes
        total_evaluated = await self.session.scalar(select(func.count()).select_from(PredictionOutcome)) or 0

        return PlatformStatsResponse(
            total_predictions=total_predictions,
            total_predictors=total_predictors,
            total_stocks=total_stocks,
            avg_accuracy_pct=avg_accuracy_pct,
            total_evaluated=total_evaluated,
        )
