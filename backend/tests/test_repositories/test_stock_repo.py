"""Tests for StockRepository CRUD and queries."""

import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stock import StockRepository
from tests.conftest import create_test_stock


async def test_get_by_symbol(db_session: AsyncSession) -> None:
    stock = await create_test_stock(db_session, symbol="RELIANCE")
    repo = StockRepository(db_session)
    found = await repo.get_by_symbol("RELIANCE")
    assert found is not None
    assert found.id == stock.id


async def test_get_by_symbol_not_found(db_session: AsyncSession) -> None:
    repo = StockRepository(db_session)
    assert await repo.get_by_symbol("NONEXIST") is None


async def test_bulk_create_skips_duplicates(db_session: AsyncSession) -> None:
    await create_test_stock(db_session, symbol="TCS")

    repo = StockRepository(db_session)
    count = await repo.bulk_create([
        {"id": uuid.uuid4(), "symbol": "TCS", "name": "TCS Ltd", "exchange": "NSE"},
        {"id": uuid.uuid4(), "symbol": "INFY", "name": "Infosys Ltd", "exchange": "NSE"},
    ])
    assert count == 1  # only INFY inserted, TCS skipped


async def test_bulk_create_empty_list(db_session: AsyncSession) -> None:
    repo = StockRepository(db_session)
    count = await repo.bulk_create([])
    assert count == 0


async def test_list_active(db_session: AsyncSession) -> None:
    await create_test_stock(db_session, symbol="ACTIVE1")
    await create_test_stock(db_session, symbol="ACTIVE2")

    repo = StockRepository(db_session)
    stocks = await repo.list_active()
    assert len(stocks) >= 2
    assert all(s.is_active for s in stocks)


async def test_list_active_pagination(db_session: AsyncSession) -> None:
    base_time = datetime(2025, 6, 1)
    for i in range(5):
        s = await create_test_stock(db_session, symbol=f"PG{i:03d}")
        s.created_at = base_time - timedelta(hours=i)
    await db_session.flush()

    repo = StockRepository(db_session)
    first = await repo.list_active(limit=3)
    assert len(first) == 3

    cursor = first[-1].created_at
    second = await repo.list_active(cursor=cursor, limit=3)
    assert len(second) == 2
