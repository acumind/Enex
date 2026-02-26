"""Login event data access repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.login_event import LoginEvent
from app.repositories.base import BaseRepository


class LoginEventRepository(BaseRepository[LoginEvent]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, LoginEvent)

    async def list_for_user(self, user_id: uuid.UUID, *, limit: int = 20) -> list[LoginEvent]:
        stmt = (
            select(LoginEvent).where(LoginEvent.user_id == user_id).order_by(LoginEvent.created_at.desc()).limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
