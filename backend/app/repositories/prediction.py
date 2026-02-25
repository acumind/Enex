"""Prediction data access repository."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction
from app.models.predictor import Predictor
from app.models.stock import Stock
from app.repositories.base import BaseRepository


class PredictionRepository(BaseRepository[Prediction]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Prediction)

    async def list_by_predictor(
        self,
        predictor_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[Prediction]:
        stmt = select(Prediction).where(Prediction.predictor_id == predictor_id).order_by(Prediction.created_at.desc())
        if cursor is not None:
            stmt = stmt.where(Prediction.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_stock(
        self,
        stock_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[Prediction]:
        stmt = select(Prediction).where(Prediction.stock_id == stock_id).order_by(Prediction.created_at.desc())
        if cursor is not None:
            stmt = stmt.where(Prediction.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_status(
        self,
        status: str,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[Prediction]:
        stmt = select(Prediction).where(Prediction.status == status).order_by(Prediction.created_at.desc())
        if cursor is not None:
            stmt = stmt.where(Prediction.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_recent(
        self,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[Prediction]:
        """List recently approved predictions."""
        stmt = select(Prediction).where(Prediction.status == "approved").order_by(Prediction.created_at.desc())
        if cursor is not None:
            stmt = stmt.where(Prediction.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[Prediction]:
        stmt = select(Prediction).where(Prediction.submitted_by == user_id).order_by(Prediction.created_at.desc())
        if cursor is not None:
            stmt = stmt.where(Prediction.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def find_duplicate(
        self,
        predictor_id: uuid.UUID,
        stock_id: uuid.UUID,
        target_price: Decimal,
        prediction_date: datetime,
    ) -> Prediction | None:
        """Find existing prediction with same predictor + stock + target ±5% + date ±30 days."""
        tolerance = target_price * Decimal("0.05")
        low = target_price - tolerance
        high = target_price + tolerance
        date_low = prediction_date - timedelta(days=30)
        date_high = prediction_date + timedelta(days=30)

        stmt = (
            select(Prediction)
            .where(
                and_(
                    Prediction.predictor_id == predictor_id,
                    Prediction.stock_id == stock_id,
                    Prediction.target_price.between(low, high),
                    Prediction.prediction_date.between(date_low, date_high),
                    Prediction.status.in_(["pending_review", "approved"]),
                )
            )
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_stock_enriched(
        self,
        stock_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[tuple[Prediction, str, str]]:
        """List predictions for a stock, joined with predictor name and slug."""
        stmt = (
            select(Prediction, Predictor.name, Predictor.slug)
            .join(Predictor, Prediction.predictor_id == Predictor.id)
            .where(Prediction.stock_id == stock_id)
            .order_by(Prediction.created_at.desc())
        )
        if cursor is not None:
            stmt = stmt.where(Prediction.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.all())

    async def list_by_predictor_enriched(
        self,
        predictor_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[tuple[Prediction, str, str]]:
        """List predictions for a predictor, joined with stock symbol and name."""
        stmt = (
            select(Prediction, Stock.symbol, Stock.name)
            .join(Stock, Prediction.stock_id == Stock.id)
            .where(Prediction.predictor_id == predictor_id)
            .order_by(Prediction.created_at.desc())
        )
        if cursor is not None:
            stmt = stmt.where(Prediction.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.all())

    async def approve(self, prediction: Prediction, reviewer_id: uuid.UUID) -> Prediction:
        prediction.status = "approved"
        prediction.reviewed_by = reviewer_id
        prediction.reviewed_at = datetime.now(UTC).replace(tzinfo=None)
        await self.session.flush()
        await self.session.refresh(prediction)
        return prediction

    async def reject(self, prediction: Prediction, reviewer_id: uuid.UUID) -> Prediction:
        prediction.status = "rejected"
        prediction.reviewed_by = reviewer_id
        prediction.reviewed_at = datetime.now(UTC).replace(tzinfo=None)
        await self.session.flush()
        await self.session.refresh(prediction)
        return prediction
