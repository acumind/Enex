"""Notification routes (authenticated)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.api.deps import get_notification_service
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.services.notification import NotificationService

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=PaginatedResponse[NotificationResponse])
async def list_notifications(
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> PaginatedResponse[NotificationResponse]:
    return await service.list_notifications(user.id, cursor=cursor, limit=limit)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def unread_count(
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> UnreadCountResponse:
    count = await service.count_unread(user.id)
    return UnreadCountResponse(count=count)


@router.post("/{notification_id}/read", status_code=204)
async def mark_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await service.mark_read(notification_id, user.id)
    await db.commit()
    return Response(status_code=204)


@router.post("/read-all", status_code=204)
async def mark_all_read(
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await service.mark_all_read(user.id)
    await db.commit()
    return Response(status_code=204)
