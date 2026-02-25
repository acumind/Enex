"""Tests for FollowRepository."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.follow import FollowRepository
from tests.conftest import create_test_predictor, create_test_user


async def test_add_and_exists(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    repo = FollowRepository(db_session)

    assert await repo.exists(user.id, predictor.id) is False
    await repo.add(user.id, predictor.id)
    assert await repo.exists(user.id, predictor.id) is True


async def test_remove_existing(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    repo = FollowRepository(db_session)
    await repo.add(user.id, predictor.id)

    removed = await repo.remove(user.id, predictor.id)
    assert removed is True
    assert await repo.exists(user.id, predictor.id) is False


async def test_remove_nonexistent(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    repo = FollowRepository(db_session)

    removed = await repo.remove(user.id, uuid.uuid4())
    assert removed is False


async def test_list_for_user(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    p1 = await create_test_predictor(db_session, name="Alpha Analyst")
    p2 = await create_test_predictor(db_session, name="Beta Analyst")
    repo = FollowRepository(db_session)

    await repo.add(user.id, p1.id)
    await repo.add(user.id, p2.id)

    rows = await repo.list_for_user(user.id)
    assert len(rows) == 2


async def test_list_for_user_with_limit(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    p1 = await create_test_predictor(db_session, name="Lim1 Analyst")
    p2 = await create_test_predictor(db_session, name="Lim2 Analyst")
    repo = FollowRepository(db_session)

    await repo.add(user.id, p1.id)
    await repo.add(user.id, p2.id)

    rows = await repo.list_for_user(user.id, limit=1)
    assert len(rows) == 1


async def test_count_for_user(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    repo = FollowRepository(db_session)

    assert await repo.count_for_user(user.id) == 0
    await repo.add(user.id, predictor.id)
    assert await repo.count_for_user(user.id) == 1


async def test_list_users_following_predictor(db_session: AsyncSession) -> None:
    user1 = await create_test_user(db_session, email="follow1@test.com")
    user2 = await create_test_user(db_session, email="follow2@test.com")
    predictor = await create_test_predictor(db_session)
    repo = FollowRepository(db_session)

    await repo.add(user1.id, predictor.id)
    await repo.add(user2.id, predictor.id)

    user_ids = await repo.list_users_following_predictor(predictor.id)
    assert len(user_ids) == 2
    assert set(user_ids) == {user1.id, user2.id}


async def test_list_users_following_predictor_empty(db_session: AsyncSession) -> None:
    repo = FollowRepository(db_session)
    user_ids = await repo.list_users_following_predictor(uuid.uuid4())
    assert user_ids == []


async def test_list_for_user_empty(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    repo = FollowRepository(db_session)
    rows = await repo.list_for_user(user.id)
    assert rows == []
