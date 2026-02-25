"""Tests for NotificationRepository."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification import Notification
from app.repositories.notification import NotificationRepository
from tests.conftest import create_test_notification, create_test_user


async def test_create_and_list(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    await create_test_notification(db_session, user_id=user.id, title="Notif 1")
    await create_test_notification(db_session, user_id=user.id, title="Notif 2")

    repo = NotificationRepository(db_session)
    items = await repo.list_for_user(user.id)
    assert len(items) == 2


async def test_count_unread(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    await create_test_notification(db_session, user_id=user.id, is_read=False)
    await create_test_notification(db_session, user_id=user.id, is_read=True)

    repo = NotificationRepository(db_session)
    count = await repo.count_unread(user.id)
    assert count == 1


async def test_mark_read(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    n = await create_test_notification(db_session, user_id=user.id, is_read=False)

    repo = NotificationRepository(db_session)
    result = await repo.mark_read(n.id, user.id)
    assert result is True

    count = await repo.count_unread(user.id)
    assert count == 0


async def test_mark_read_wrong_user(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    n = await create_test_notification(db_session, user_id=user.id)

    repo = NotificationRepository(db_session)
    result = await repo.mark_read(n.id, uuid.uuid4())
    assert result is False


async def test_mark_all_read(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    await create_test_notification(db_session, user_id=user.id, is_read=False)
    await create_test_notification(db_session, user_id=user.id, is_read=False)

    repo = NotificationRepository(db_session)
    marked = await repo.mark_all_read(user.id)
    assert marked == 2

    count = await repo.count_unread(user.id)
    assert count == 0


async def test_create_bulk(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    repo = NotificationRepository(db_session)

    notifications = [
        Notification(
            user_id=user.id,
            type="test",
            title=f"Bulk {i}",
            data={},
        )
        for i in range(3)
    ]

    count = await repo.create_bulk(notifications)
    assert count == 3

    items = await repo.list_for_user(user.id)
    assert len(items) == 3


async def test_create_bulk_empty(db_session: AsyncSession) -> None:
    repo = NotificationRepository(db_session)
    count = await repo.create_bulk([])
    assert count == 0


async def test_list_for_user_with_limit(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    for i in range(5):
        await create_test_notification(db_session, user_id=user.id, title=f"N{i}")

    repo = NotificationRepository(db_session)
    items = await repo.list_for_user(user.id, limit=3)
    assert len(items) == 3
