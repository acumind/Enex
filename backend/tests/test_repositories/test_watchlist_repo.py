"""Tests for WatchlistRepository."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.watchlist import WatchlistRepository
from tests.conftest import create_test_stock, create_test_user


async def test_add_and_exists(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock = await create_test_stock(db_session)
    repo = WatchlistRepository(db_session)

    assert await repo.exists(user.id, stock.id) is False
    await repo.add(user.id, stock.id)
    assert await repo.exists(user.id, stock.id) is True


async def test_remove_existing(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock = await create_test_stock(db_session)
    repo = WatchlistRepository(db_session)
    await repo.add(user.id, stock.id)

    removed = await repo.remove(user.id, stock.id)
    assert removed is True
    assert await repo.exists(user.id, stock.id) is False


async def test_remove_nonexistent(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    repo = WatchlistRepository(db_session)

    removed = await repo.remove(user.id, uuid.uuid4())
    assert removed is False


async def test_list_for_user(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock1 = await create_test_stock(db_session, symbol="AAA1")
    stock2 = await create_test_stock(db_session, symbol="BBB2")
    repo = WatchlistRepository(db_session)

    await repo.add(user.id, stock1.id)
    await repo.add(user.id, stock2.id)

    rows = await repo.list_for_user(user.id)
    assert len(rows) == 2


async def test_list_for_user_with_limit(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock1 = await create_test_stock(db_session, symbol="LIM1")
    stock2 = await create_test_stock(db_session, symbol="LIM2")
    repo = WatchlistRepository(db_session)

    await repo.add(user.id, stock1.id)
    await repo.add(user.id, stock2.id)

    rows = await repo.list_for_user(user.id, limit=1)
    assert len(rows) == 1


async def test_count_for_user(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock = await create_test_stock(db_session)
    repo = WatchlistRepository(db_session)

    assert await repo.count_for_user(user.id) == 0
    await repo.add(user.id, stock.id)
    assert await repo.count_for_user(user.id) == 1


async def test_list_users_watching_stock(db_session: AsyncSession) -> None:
    user1 = await create_test_user(db_session, email="watch1@test.com")
    user2 = await create_test_user(db_session, email="watch2@test.com")
    stock = await create_test_stock(db_session)
    repo = WatchlistRepository(db_session)

    await repo.add(user1.id, stock.id)
    await repo.add(user2.id, stock.id)

    user_ids = await repo.list_users_watching_stock(stock.id)
    assert len(user_ids) == 2
    assert set(user_ids) == {user1.id, user2.id}


async def test_list_users_watching_stock_empty(db_session: AsyncSession) -> None:
    repo = WatchlistRepository(db_session)
    user_ids = await repo.list_users_watching_stock(uuid.uuid4())
    assert user_ids == []


async def test_list_for_user_empty(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    repo = WatchlistRepository(db_session)
    rows = await repo.list_for_user(user.id)
    assert rows == []
