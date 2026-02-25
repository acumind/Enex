"""Notification business logic."""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.notification import Notification
from app.repositories.notification import NotificationRepository
from app.schemas.common import PaginatedResponse
from app.schemas.notification import NotificationResponse


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = NotificationRepository(session)

    async def create_notification(
        self,
        user_id: uuid.UUID,
        type: str,
        title: str,
        message: str | None = None,
        data: dict[str, str] | None = None,
    ) -> NotificationResponse:
        notification = Notification(
            user_id=user_id,
            type=type,
            title=title,
            message=message,
            data=data or {},
        )
        notification = await self.repo.create(notification)
        return NotificationResponse.model_validate(notification)

    async def list_notifications(
        self,
        user_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[NotificationResponse]:
        notifications = await self.repo.list_for_user(user_id, cursor=cursor, limit=limit + 1)
        has_more = len(notifications) > limit
        if has_more:
            notifications = notifications[:limit]

        items = [NotificationResponse.model_validate(n) for n in notifications]
        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[NotificationResponse](items=items, next_cursor=next_cursor, has_more=has_more)

    async def count_unread(self, user_id: uuid.UUID) -> int:
        return await self.repo.count_unread(user_id)

    async def mark_read(self, notification_id: uuid.UUID, user_id: uuid.UUID) -> None:
        marked = await self.repo.mark_read(notification_id, user_id)
        if not marked:
            raise NotFoundError("Notification not found")

    async def mark_all_read(self, user_id: uuid.UUID) -> int:
        return await self.repo.mark_all_read(user_id)
