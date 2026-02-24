"""Suggestion service — create, list, promote, dismiss prediction suggestions."""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleViolation, NotFoundError
from app.models.prediction import PredictionSuggestion
from app.repositories.suggestion import SuggestionRepository
from app.schemas.common import PaginatedResponse
from app.schemas.suggestion import SuggestionCreate, SuggestionResponse


class SuggestionService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = SuggestionRepository(session)

    async def create(self, data: SuggestionCreate, submitted_by: uuid.UUID) -> SuggestionResponse:
        suggestion = PredictionSuggestion(
            url=data.url,
            note=data.note,
            submitted_by=submitted_by,
            status="pending",
        )
        suggestion = await self.repo.create(suggestion)
        return SuggestionResponse.model_validate(suggestion)

    async def list_pending(
        self,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[SuggestionResponse]:
        suggestions = await self.repo.list_by_status("pending", cursor=cursor, limit=limit + 1)
        has_more = len(suggestions) > limit
        if has_more:
            suggestions = suggestions[:limit]

        items = [SuggestionResponse.model_validate(s) for s in suggestions]
        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[SuggestionResponse](items=items, next_cursor=next_cursor, has_more=has_more)

    async def promote(self, suggestion_id: uuid.UUID, reviewer_id: uuid.UUID) -> SuggestionResponse:
        suggestion = await self.repo.get_by_id(suggestion_id)
        if suggestion is None:
            raise NotFoundError("Suggestion not found")
        if suggestion.status != "pending":
            raise BusinessRuleViolation(f"Cannot promote suggestion with status '{suggestion.status}'")

        # Dispatch Celery extraction task
        from app.jobs.extraction import extract_prediction_task

        extract_prediction_task.delay(str(suggestion_id), str(reviewer_id), suggestion.url)

        # Mark as promoted (promoted_to will be set by the background task)
        suggestion.status = "promoted"
        suggestion.reviewed_by = reviewer_id
        from datetime import UTC

        suggestion.reviewed_at = datetime.now(UTC).replace(tzinfo=None)
        await self.repo.session.flush()
        await self.repo.session.refresh(suggestion)
        return SuggestionResponse.model_validate(suggestion)

    async def dismiss(self, suggestion_id: uuid.UUID, reviewer_id: uuid.UUID) -> SuggestionResponse:
        suggestion = await self.repo.get_by_id(suggestion_id)
        if suggestion is None:
            raise NotFoundError("Suggestion not found")
        if suggestion.status != "pending":
            raise BusinessRuleViolation(f"Cannot dismiss suggestion with status '{suggestion.status}'")

        suggestion = await self.repo.dismiss(suggestion, reviewer_id)
        return SuggestionResponse.model_validate(suggestion)
