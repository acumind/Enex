"""Notification data access repository."""

import uuid

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Notification)

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        cursor: str | None = None,
        limit: int = 20,
    ) -> list[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id).order_by(Notification.created_at.desc())
        if cursor is not None:
            stmt = stmt.where(Notification.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_unread(self, user_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(Notification)
            .where(and_(Notification.user_id == user_id, Notification.is_read.is_(False)))
        )
        return result.scalar_one()

    async def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            update(Notification)
            .where(and_(Notification.id == notification_id, Notification.user_id == user_id))
            .values(is_read=True)
        )
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        result = await self.session.execute(
            update(Notification)
            .where(and_(Notification.user_id == user_id, Notification.is_read.is_(False)))
            .values(is_read=True)
        )
        await self.session.flush()
        return result.rowcount  # type: ignore[return-value]

    async def create_bulk(self, notifications: list[Notification]) -> int:
        if not notifications:
            return 0
        self.session.add_all(notifications)
        await self.session.flush()
        return len(notifications)
