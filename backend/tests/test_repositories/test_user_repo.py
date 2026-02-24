"""Tests for UserRepository CRUD and queries."""

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.user import UserRepository
from tests.conftest import create_test_admin, create_test_user


async def test_get_by_email(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session, email="lookup@example.com")
    repo = UserRepository(db_session)
    found = await repo.get_by_email("lookup@example.com")
    assert found is not None
    assert found.id == user.id


async def test_get_by_email_not_found(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    found = await repo.get_by_email("nonexistent@example.com")
    assert found is None


async def test_get_by_phone(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session, phone="+919876543210")
    repo = UserRepository(db_session)
    found = await repo.get_by_phone("+919876543210")
    assert found is not None
    assert found.id == user.id


async def test_list_users_pagination(db_session: AsyncSession) -> None:
    base_time = datetime(2025, 6, 1)
    for i in range(5):
        user = await create_test_user(db_session, email=f"page-{i}@example.com")
        # Set explicit timestamps so cursor pagination works within single txn
        user.created_at = base_time - timedelta(hours=i)
    await db_session.flush()

    repo = UserRepository(db_session)
    first_page = await repo.list_users(limit=3)
    assert len(first_page) == 3

    cursor = first_page[-1].created_at
    second_page = await repo.list_users(cursor=cursor, limit=3)
    assert len(second_page) == 2


async def test_count_admins(db_session: AsyncSession) -> None:
    await create_test_admin(db_session)
    await create_test_admin(db_session)
    await create_test_user(db_session, role="user")

    repo = UserRepository(db_session)
    count = await repo.count_admins()
    assert count == 2


async def test_create_and_get_by_id(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    user = User(email="new@example.com", name="New User", role="user")
    created = await repo.create(user)
    assert created.id is not None

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.email == "new@example.com"


async def test_update_user(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    repo = UserRepository(db_session)
    await repo.update(user, {"name": "Updated Name"})
    assert user.name == "Updated Name"


async def test_delete_user(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    repo = UserRepository(db_session)
    await repo.delete(user)
    assert await repo.get_by_id(user.id) is None
