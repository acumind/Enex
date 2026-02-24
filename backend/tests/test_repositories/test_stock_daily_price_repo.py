"""Tests for StockDailyPriceRepository."""

from datetime import date
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.stock_daily_price import StockDailyPriceRepository
from tests.conftest import create_test_stock, create_test_stock_daily_price


async def test_bulk_upsert_insert(db_session: AsyncSession) -> None:
    stock = await create_test_stock(db_session)
    repo = StockDailyPriceRepository(db_session)

    data = [
        {
            "stock_id": stock.id,
            "trade_date": date(2025, 1, 15),
            "close_price": Decimal("1200.00"),
            "open_price": Decimal("1190.00"),
            "high_price": Decimal("1220.00"),
            "low_price": Decimal("1180.00"),
            "volume": 1000000,
            "adjusted_close": Decimal("1198.00"),
        },
        {
            "stock_id": stock.id,
            "trade_date": date(2025, 1, 16),
            "close_price": Decimal("1210.00"),
            "open_price": None,
            "high_price": None,
            "low_price": None,
            "volume": None,
            "adjusted_close": None,
        },
    ]
    count = await repo.bulk_upsert(data)
    assert count == 2


async def test_bulk_upsert_update(db_session: AsyncSession) -> None:
    stock = await create_test_stock(db_session)
    await create_test_stock_daily_price(
        db_session, stock_id=stock.id, trade_date=date(2025, 1, 15), close_price=Decimal("1200.00")
    )

    repo = StockDailyPriceRepository(db_session)
    data = [
        {
            "stock_id": stock.id,
            "trade_date": date(2025, 1, 15),
            "close_price": Decimal("1250.00"),
            "open_price": None,
            "high_price": None,
            "low_price": None,
            "volume": None,
            "adjusted_close": None,
        },
    ]
    count = await repo.bulk_upsert(data)
    assert count == 1

    # Verify updated
    price = await repo.get_price_on_date(stock.id, date(2025, 1, 15))
    assert price is not None
    assert price.close_price == Decimal("1250.00")


async def test_bulk_upsert_empty(db_session: AsyncSession) -> None:
    repo = StockDailyPriceRepository(db_session)
    count = await repo.bulk_upsert([])
    assert count == 0


async def test_get_price_on_date_exact(db_session: AsyncSession) -> None:
    stock = await create_test_stock(db_session)
    await create_test_stock_daily_price(
        db_session, stock_id=stock.id, trade_date=date(2025, 1, 15), close_price=Decimal("1200.00")
    )

    repo = StockDailyPriceRepository(db_session)
    price = await repo.get_price_on_date(stock.id, date(2025, 1, 15))
    assert price is not None
    assert price.close_price == Decimal("1200.00")


async def test_get_price_on_date_nearest_prior(db_session: AsyncSession) -> None:
    """Weekend/holiday: should return the most recent prior trading day."""
    stock = await create_test_stock(db_session)
    await create_test_stock_daily_price(
        db_session, stock_id=stock.id, trade_date=date(2025, 1, 17), close_price=Decimal("1300.00")
    )

    repo = StockDailyPriceRepository(db_session)
    # Ask for Sunday Jan 19 — should get Friday Jan 17
    price = await repo.get_price_on_date(stock.id, date(2025, 1, 19))
    assert price is not None
    assert price.trade_date == date(2025, 1, 17)
    assert price.close_price == Decimal("1300.00")


async def test_get_price_on_date_no_data(db_session: AsyncSession) -> None:
    stock = await create_test_stock(db_session)
    repo = StockDailyPriceRepository(db_session)
    price = await repo.get_price_on_date(stock.id, date(2025, 1, 15))
    assert price is None


async def test_get_high_low_in_range(db_session: AsyncSession) -> None:
    stock = await create_test_stock(db_session)
    await create_test_stock_daily_price(
        db_session,
        stock_id=stock.id,
        trade_date=date(2025, 1, 15),
        close_price=Decimal("1200.00"),
        adjusted_close=Decimal("1198.00"),
    )
    await create_test_stock_daily_price(
        db_session,
        stock_id=stock.id,
        trade_date=date(2025, 1, 16),
        close_price=Decimal("1300.00"),
        adjusted_close=Decimal("1298.00"),
    )
    await create_test_stock_daily_price(
        db_session,
        stock_id=stock.id,
        trade_date=date(2025, 1, 17),
        close_price=Decimal("1100.00"),
        adjusted_close=Decimal("1098.00"),
    )

    repo = StockDailyPriceRepository(db_session)
    highest, lowest = await repo.get_high_low_in_range(stock.id, date(2025, 1, 15), date(2025, 1, 17))
    # Should prefer adjusted_close
    assert highest == Decimal("1298.00")
    assert lowest == Decimal("1098.00")


async def test_get_high_low_in_range_no_adjusted(db_session: AsyncSession) -> None:
    """Falls back to close_price when adjusted_close is None."""
    stock = await create_test_stock(db_session)
    await create_test_stock_daily_price(
        db_session,
        stock_id=stock.id,
        trade_date=date(2025, 1, 15),
        close_price=Decimal("1200.00"),
    )
    await create_test_stock_daily_price(
        db_session,
        stock_id=stock.id,
        trade_date=date(2025, 1, 16),
        close_price=Decimal("1400.00"),
    )

    repo = StockDailyPriceRepository(db_session)
    highest, lowest = await repo.get_high_low_in_range(stock.id, date(2025, 1, 15), date(2025, 1, 16))
    assert highest == Decimal("1400.00")
    assert lowest == Decimal("1200.00")


async def test_get_latest_date_per_stock(db_session: AsyncSession) -> None:
    stock1 = await create_test_stock(db_session, symbol="AAA")
    stock2 = await create_test_stock(db_session, symbol="BBB")
    await create_test_stock_daily_price(db_session, stock_id=stock1.id, trade_date=date(2025, 1, 15))
    await create_test_stock_daily_price(db_session, stock_id=stock1.id, trade_date=date(2025, 1, 17))
    await create_test_stock_daily_price(db_session, stock_id=stock2.id, trade_date=date(2025, 1, 10))

    repo = StockDailyPriceRepository(db_session)
    latest = await repo.get_latest_date_per_stock([stock1.id, stock2.id])
    assert latest[stock1.id] == date(2025, 1, 17)
    assert latest[stock2.id] == date(2025, 1, 10)


async def test_get_latest_date_per_stock_empty(db_session: AsyncSession) -> None:
    repo = StockDailyPriceRepository(db_session)
    latest = await repo.get_latest_date_per_stock([])
    assert latest == {}
