"""Tests for NotificationService."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.services.notification import NotificationService
from tests.conftest import create_test_notification, create_test_user


async def test_create_notification(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    service = NotificationService(db_session)

    resp = await service.create_notification(user.id, "test_type", "Test Title", "Test body", {"key": "val"})
    assert resp.title == "Test Title"
    assert resp.type == "test_type"


async def test_list_notifications(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    await create_test_notification(db_session, user_id=user.id)
    await create_test_notification(db_session, user_id=user.id)

    service = NotificationService(db_session)
    result = await service.list_notifications(user.id)
    assert len(result.items) == 2


async def test_count_unread(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    await create_test_notification(db_session, user_id=user.id, is_read=False)
    await create_test_notification(db_session, user_id=user.id, is_read=True)

    service = NotificationService(db_session)
    assert await service.count_unread(user.id) == 1


async def test_mark_read(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    n = await create_test_notification(db_session, user_id=user.id, is_read=False)

    service = NotificationService(db_session)
    await service.mark_read(n.id, user.id)
    assert await service.count_unread(user.id) == 0


async def test_mark_read_not_found(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    service = NotificationService(db_session)

    with pytest.raises(NotFoundError):
        await service.mark_read(uuid.uuid4(), user.id)


async def test_mark_all_read(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    await create_test_notification(db_session, user_id=user.id, is_read=False)
    await create_test_notification(db_session, user_id=user.id, is_read=False)

    service = NotificationService(db_session)
    count = await service.mark_all_read(user.id)
    assert count == 2
    assert await service.count_unread(user.id) == 0
