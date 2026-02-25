"""Follow predictor business logic."""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.follow import FollowRepository
from app.repositories.predictor import PredictorRepository
from app.schemas.common import PaginatedResponse
from app.schemas.engagement import FollowItemEnriched


class FollowService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = FollowRepository(session)
        self.predictor_repo = PredictorRepository(session)

    async def add(self, user_id: uuid.UUID, predictor_id: uuid.UUID) -> None:
        predictor = await self.predictor_repo.get_by_id(predictor_id)
        if predictor is None:
            raise NotFoundError("Predictor not found")
        if await self.repo.exists(user_id, predictor_id):
            raise ConflictError("Already following this predictor")
        await self.repo.add(user_id, predictor_id)

    async def remove(self, user_id: uuid.UUID, predictor_id: uuid.UUID) -> None:
        removed = await self.repo.remove(user_id, predictor_id)
        if not removed:
            raise NotFoundError("Not following this predictor")

    async def check(self, user_id: uuid.UUID, predictor_id: uuid.UUID) -> bool:
        return await self.repo.exists(user_id, predictor_id)

    async def list_following(
        self,
        user_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[FollowItemEnriched]:
        rows = await self.repo.list_for_user(user_id, cursor=cursor, limit=limit + 1)
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = [
            FollowItemEnriched(
                user_id=entry.user_id,
                predictor_id=entry.predictor_id,
                created_at=entry.created_at,
                predictor_name=predictor.name,
                predictor_slug=predictor.slug,
                predictor_type=predictor.type,
                predictor_is_verified=predictor.is_verified,
            )
            for entry, predictor in rows
        ]
        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[FollowItemEnriched](items=items, next_cursor=next_cursor, has_more=has_more)
