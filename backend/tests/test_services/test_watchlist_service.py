"""Tests for WatchlistService."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.services.watchlist import WatchlistService
from tests.conftest import create_test_stock, create_test_user


async def test_add_stock(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock = await create_test_stock(db_session)
    service = WatchlistService(db_session)

    await service.add(user.id, stock.id)
    assert await service.check(user.id, stock.id) is True


async def test_add_stock_not_found(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    service = WatchlistService(db_session)

    with pytest.raises(NotFoundError):
        await service.add(user.id, uuid.uuid4())


async def test_add_duplicate_raises_conflict(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock = await create_test_stock(db_session)
    service = WatchlistService(db_session)

    await service.add(user.id, stock.id)
    with pytest.raises(ConflictError):
        await service.add(user.id, stock.id)


async def test_remove_stock(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock = await create_test_stock(db_session)
    service = WatchlistService(db_session)

    await service.add(user.id, stock.id)
    await service.remove(user.id, stock.id)
    assert await service.check(user.id, stock.id) is False


async def test_remove_not_watching_raises_not_found(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    service = WatchlistService(db_session)

    with pytest.raises(NotFoundError):
        await service.remove(user.id, uuid.uuid4())


async def test_check_not_watching(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    service = WatchlistService(db_session)

    assert await service.check(user.id, uuid.uuid4()) is False


async def test_list_watchlist(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock = await create_test_stock(db_session)
    service = WatchlistService(db_session)

    await service.add(user.id, stock.id)
    result = await service.list_watchlist(user.id)

    assert len(result.items) == 1
    assert result.items[0].stock_symbol == stock.symbol
    assert result.has_more is False


async def test_list_watchlist_empty(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    service = WatchlistService(db_session)

    result = await service.list_watchlist(user.id)
    assert result.items == []
