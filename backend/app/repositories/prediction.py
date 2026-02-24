"""Prediction data access repository."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction
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
        stmt = (
            select(Prediction)
            .where(Prediction.predictor_id == predictor_id)
            .order_by(Prediction.created_at.desc())
        )
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
        stmt = (
            select(Prediction)
            .where(Prediction.stock_id == stock_id)
            .order_by(Prediction.created_at.desc())
        )
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
        stmt = (
            select(Prediction)
            .where(Prediction.status == status)
            .order_by(Prediction.created_at.desc())
        )
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
        stmt = (
            select(Prediction)
            .where(Prediction.status == "approved")
            .order_by(Prediction.created_at.desc())
        )
        if cursor is not None:
            stmt = stmt.where(Prediction.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

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
