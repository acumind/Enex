"""Suggestion data access repository."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import PredictionSuggestion
from app.repositories.base import BaseRepository


class SuggestionRepository(BaseRepository[PredictionSuggestion]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PredictionSuggestion)

    async def list_by_status(
        self,
        status: str,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[PredictionSuggestion]:
        stmt = (
            select(PredictionSuggestion)
            .where(PredictionSuggestion.status == status)
            .order_by(PredictionSuggestion.created_at.desc())
        )
        if cursor is not None:
            stmt = stmt.where(PredictionSuggestion.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[PredictionSuggestion]:
        stmt = (
            select(PredictionSuggestion)
            .where(PredictionSuggestion.submitted_by == user_id)
            .order_by(PredictionSuggestion.created_at.desc())
        )
        if cursor is not None:
            stmt = stmt.where(PredictionSuggestion.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def promote(
        self,
        suggestion: PredictionSuggestion,
        prediction_id: uuid.UUID,
        reviewer_id: uuid.UUID,
    ) -> PredictionSuggestion:
        suggestion.status = "promoted"
        suggestion.promoted_to = prediction_id
        suggestion.reviewed_by = reviewer_id
        suggestion.reviewed_at = datetime.now(UTC).replace(tzinfo=None)
        await self.session.flush()
        await self.session.refresh(suggestion)
        return suggestion

    async def dismiss(
        self,
        suggestion: PredictionSuggestion,
        reviewer_id: uuid.UUID,
    ) -> PredictionSuggestion:
        suggestion.status = "dismissed"
        suggestion.reviewed_by = reviewer_id
        suggestion.reviewed_at = datetime.now(UTC).replace(tzinfo=None)
        await self.session.flush()
        await self.session.refresh(suggestion)
        return suggestion
