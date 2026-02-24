"""PredictionOutcome data access repository."""

import uuid
from datetime import date

from sqlalchemy import and_, func, not_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction, PredictionOutcome
from app.repositories.base import BaseRepository


class OutcomeRepository(BaseRepository[PredictionOutcome]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PredictionOutcome)

    async def get_by_prediction_id(self, prediction_id: uuid.UUID) -> PredictionOutcome | None:
        stmt = select(PredictionOutcome).where(PredictionOutcome.prediction_id == prediction_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_ready_for_evaluation(self, as_of_date: date) -> list[Prediction]:
        """Find approved predictions whose eval date has passed and have no outcome yet."""
        outcome_exists = select(PredictionOutcome.prediction_id).where(PredictionOutcome.prediction_id == Prediction.id)
        stmt = (
            select(Prediction)
            .where(
                and_(
                    Prediction.status == "approved",
                    Prediction.default_eval_date <= as_of_date,
                    not_(outcome_exists.exists()),
                )
            )
            .order_by(Prediction.default_eval_date)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_predictor(
        self,
        predictor_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[PredictionOutcome]:
        stmt = (
            select(PredictionOutcome)
            .join(Prediction, PredictionOutcome.prediction_id == Prediction.id)
            .where(Prediction.predictor_id == predictor_id)
            .order_by(PredictionOutcome.evaluated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_stock(
        self,
        stock_id: uuid.UUID,
        *,
        limit: int = 50,
    ) -> list[PredictionOutcome]:
        stmt = (
            select(PredictionOutcome)
            .join(Prediction, PredictionOutcome.prediction_id == Prediction.id)
            .where(Prediction.stock_id == stock_id)
            .order_by(PredictionOutcome.evaluated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_status_for_predictor(self, predictor_id: uuid.UUID) -> dict[str, int]:
        """Get aggregated outcome counts for a predictor."""
        stmt = (
            select(
                PredictionOutcome.outcome_status,
                func.count().label("cnt"),
            )
            .join(Prediction, PredictionOutcome.prediction_id == Prediction.id)
            .where(Prediction.predictor_id == predictor_id)
            .group_by(PredictionOutcome.outcome_status)
        )
        result = await self.session.execute(stmt)
        return {row.outcome_status: row.cnt for row in result.all()}
