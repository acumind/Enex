"""StockDailyPrice data access repository."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import StockDailyPrice
from app.repositories.base import BaseRepository


class StockDailyPriceRepository(BaseRepository[StockDailyPrice]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, StockDailyPrice)

    async def bulk_upsert(self, prices_data: list[dict[str, object]]) -> int:
        """Insert or update daily prices. Returns number of rows affected."""
        if not prices_data:
            return 0
        stmt = (
            pg_insert(StockDailyPrice)
            .values(prices_data)
            .on_conflict_do_update(
                constraint="uq_stock_daily_prices_stock_date",
                set_={
                    "open_price": pg_insert(StockDailyPrice).excluded.open_price,
                    "high_price": pg_insert(StockDailyPrice).excluded.high_price,
                    "low_price": pg_insert(StockDailyPrice).excluded.low_price,
                    "close_price": pg_insert(StockDailyPrice).excluded.close_price,
                    "volume": pg_insert(StockDailyPrice).excluded.volume,
                    "adjusted_close": pg_insert(StockDailyPrice).excluded.adjusted_close,
                },
            )
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return int(result.rowcount)  # type: ignore[attr-defined]

    async def get_price_on_date(self, stock_id: uuid.UUID, target_date: date) -> StockDailyPrice | None:
        """Get price on or before a date (handles weekends/holidays)."""
        stmt = (
            select(StockDailyPrice)
            .where(
                StockDailyPrice.stock_id == stock_id,
                StockDailyPrice.trade_date <= target_date,
            )
            .order_by(StockDailyPrice.trade_date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_high_low_in_range(
        self, stock_id: uuid.UUID, start_date: date, end_date: date
    ) -> tuple[Decimal | None, Decimal | None]:
        """Get the highest and lowest adjusted/close price in a date range."""
        price_col = func.coalesce(StockDailyPrice.adjusted_close, StockDailyPrice.close_price)
        stmt = select(
            func.max(price_col).label("highest"),
            func.min(price_col).label("lowest"),
        ).where(
            StockDailyPrice.stock_id == stock_id,
            StockDailyPrice.trade_date.between(start_date, end_date),
        )
        result = await self.session.execute(stmt)
        row = result.one()
        return row.highest, row.lowest

    async def get_price_range(self, stock_id: uuid.UUID, start_date: date, end_date: date) -> list[StockDailyPrice]:
        """Get all daily prices in a date range."""
        stmt = (
            select(StockDailyPrice)
            .where(
                StockDailyPrice.stock_id == stock_id,
                StockDailyPrice.trade_date.between(start_date, end_date),
            )
            .order_by(StockDailyPrice.trade_date)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_latest_date_per_stock(self, stock_ids: list[uuid.UUID]) -> dict[uuid.UUID, date]:
        """Get the most recent trade date for each stock. For incremental fetching."""
        if not stock_ids:
            return {}
        stmt = (
            select(
                StockDailyPrice.stock_id,
                func.max(StockDailyPrice.trade_date).label("latest_date"),
            )
            .where(StockDailyPrice.stock_id.in_(stock_ids))
            .group_by(StockDailyPrice.stock_id)
        )
        result = await self.session.execute(stmt)
        return {row.stock_id: row.latest_date for row in result.all()}
