"""Follow data access repository (composite PK — does not extend BaseRepository)."""

import uuid
from datetime import datetime

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.engagement import UserFollowedPredictor
from app.models.predictor import Predictor


class FollowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, user_id: uuid.UUID, predictor_id: uuid.UUID) -> UserFollowedPredictor:
        entry = UserFollowedPredictor(user_id=user_id, predictor_id=predictor_id)
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def remove(self, user_id: uuid.UUID, predictor_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(UserFollowedPredictor).where(
                and_(
                    UserFollowedPredictor.user_id == user_id,
                    UserFollowedPredictor.predictor_id == predictor_id,
                )
            )
        )
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]

    async def exists(self, user_id: uuid.UUID, predictor_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(func.count())
            .select_from(UserFollowedPredictor)
            .where(
                and_(
                    UserFollowedPredictor.user_id == user_id,
                    UserFollowedPredictor.predictor_id == predictor_id,
                )
            )
        )
        return result.scalar_one() > 0

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[tuple[UserFollowedPredictor, Predictor]]:
        stmt = (
            select(UserFollowedPredictor, Predictor)
            .join(Predictor, UserFollowedPredictor.predictor_id == Predictor.id)
            .where(UserFollowedPredictor.user_id == user_id)
            .order_by(UserFollowedPredictor.created_at.desc())
        )
        if cursor is not None:
            stmt = stmt.where(UserFollowedPredictor.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.all())

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(UserFollowedPredictor).where(UserFollowedPredictor.user_id == user_id)
        )
        return result.scalar_one()

    async def list_users_following_predictor(self, predictor_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self.session.execute(
            select(UserFollowedPredictor.user_id).where(UserFollowedPredictor.predictor_id == predictor_id)
        )
        return [row[0] for row in result.all()]
