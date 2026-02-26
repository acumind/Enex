"""Platform statistics aggregation service."""

from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cached_response
from app.models.prediction import Prediction, PredictionOutcome, PredictionSuggestion
from app.models.predictor import Predictor
from app.models.scorecard import PredictorScorecard
from app.models.stock import Stock
from app.models.user import User
from app.schemas.stats import AdminStatsResponse, PlatformStatsResponse


class StatsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_admin_stats(self) -> AdminStatsResponse:
        pending_predictions = (
            await self.session.scalar(
                select(func.count()).select_from(Prediction).where(Prediction.status == "pending_review")
            )
            or 0
        )
        pending_suggestions = (
            await self.session.scalar(
                select(func.count()).select_from(PredictionSuggestion).where(PredictionSuggestion.status == "pending")
            )
            or 0
        )
        total_users = await self.session.scalar(select(func.count()).select_from(User)) or 0
        total_predictors = await self.session.scalar(select(func.count()).select_from(Predictor)) or 0
        total_stocks = await self.session.scalar(select(func.count()).select_from(Stock)) or 0

        now = datetime.now(UTC).replace(tzinfo=None)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())

        predictions_today = (
            await self.session.scalar(
                select(func.count()).select_from(Prediction).where(Prediction.created_at >= today_start)
            )
            or 0
        )
        predictions_this_week = (
            await self.session.scalar(
                select(func.count()).select_from(Prediction).where(Prediction.created_at >= week_start)
            )
            or 0
        )

        return AdminStatsResponse(
            pending_predictions=pending_predictions,
            pending_suggestions=pending_suggestions,
            total_users=total_users,
            total_predictors=total_predictors,
            total_stocks=total_stocks,
            predictions_today=predictions_today,
            predictions_this_week=predictions_this_week,
        )

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
