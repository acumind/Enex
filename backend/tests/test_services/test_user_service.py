"""Tests for UserService: role changes, last-admin protection, ban/unban."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleViolation, NotFoundError
from app.services.user import UserService
from tests.conftest import create_test_admin, create_test_user


async def test_list_users(db_session: AsyncSession) -> None:
    for i in range(3):
        await create_test_user(db_session, email=f"list-{i}@example.com")

    service = UserService(db_session)
    result = await service.list_users(limit=10)
    assert len(result.items) == 3
    assert result.has_more is False


async def test_change_role(db_session: AsyncSession) -> None:
    # Need at least 2 admins so we can demote one
    admin1 = await create_test_admin(db_session)
    await create_test_admin(db_session)

    service = UserService(db_session)
    result = await service.change_role(admin1.id, "moderator")
    assert result.role == "moderator"


async def test_change_role_last_admin_protection(db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)

    service = UserService(db_session)
    with pytest.raises(BusinessRuleViolation, match="Cannot demote the last admin"):
        await service.change_role(admin.id, "user")


async def test_change_role_user_not_found(db_session: AsyncSession) -> None:
    service = UserService(db_session)
    with pytest.raises(NotFoundError):
        await service.change_role(uuid.uuid4(), "admin")


async def test_ban_user(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)

    service = UserService(db_session)
    result = await service.ban_user(user.id, "Spam")
    assert result.is_active is False


async def test_unban_user(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session, is_active=False)

    service = UserService(db_session)
    result = await service.unban_user(user.id)
    assert result.is_active is True


async def test_create_admin_new_user(db_session: AsyncSession) -> None:
    service = UserService(db_session)
    user = await service.create_admin("newadmin@example.com")
    assert user.role == "admin"
    assert user.email == "newadmin@example.com"


async def test_create_admin_promotes_existing(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session, email="promote@example.com", role="user")

    service = UserService(db_session)
    result = await service.create_admin("promote@example.com")
    assert result.role == "admin"
    assert result.id == user.id
