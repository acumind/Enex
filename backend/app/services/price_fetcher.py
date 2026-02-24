"""Price fetcher service — orchestrates stock price data retrieval and storage."""

import logging
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.price_data.yfinance_adapter import YFinanceAdapter
from app.models.stock import Stock
from app.repositories.stock_daily_price import StockDailyPriceRepository

logger = logging.getLogger(__name__)

# Initial lookback when no price data exists for a stock
_INITIAL_LOOKBACK_DAYS = 730  # ~2 years


class PriceFetcherService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.price_repo = StockDailyPriceRepository(session)
        self.adapter = YFinanceAdapter()

    async def fetch_all_active_stocks(self) -> int:
        """Incrementally fetch daily prices for all active stocks. Returns total rows upserted."""
        # Get all active stocks
        stmt = select(Stock).where(Stock.is_active.is_(True))
        result = await self.session.execute(stmt)
        stocks = list(result.scalars().all())
        if not stocks:
            return 0

        stock_ids = [s.id for s in stocks]
        latest_dates = await self.price_repo.get_latest_date_per_stock(stock_ids)

        today = date.today()
        total_upserted = 0

        for stock in stocks:
            last_date = latest_dates.get(stock.id)
            if last_date is not None:
                start_date = last_date + timedelta(days=1)
            else:
                start_date = today - timedelta(days=_INITIAL_LOOKBACK_DAYS)

            if start_date > today:
                continue

            prices = await self.adapter.fetch_historical(stock.symbol, start_date, today)
            if not prices:
                continue

            prices_data = [
                {
                    "stock_id": stock.id,
                    "trade_date": p.trade_date,
                    "open_price": p.open_price,
                    "high_price": p.high_price,
                    "low_price": p.low_price,
                    "close_price": p.close_price,
                    "volume": p.volume,
                    "adjusted_close": p.adjusted_close,
                }
                for p in prices
            ]
            count = await self.price_repo.bulk_upsert(prices_data)
            total_upserted += count
            logger.info("Fetched %d prices for %s", count, stock.symbol)

        return total_upserted

    async def update_current_prices(self) -> int:
        """Batch fetch current prices and update stocks table. Returns count updated."""
        stmt = select(Stock).where(Stock.is_active.is_(True))
        result = await self.session.execute(stmt)
        stocks = list(result.scalars().all())
        if not stocks:
            return 0

        symbols = [s.symbol for s in stocks]
        current_prices = await self.adapter.fetch_current_prices(symbols)

        now = datetime.now(UTC).replace(tzinfo=None)
        updated = 0
        for stock in stocks:
            price = current_prices.get(stock.symbol)
            if price is not None:
                stock.current_price = price
                stock.price_updated_at = now
                updated += 1

        await self.session.flush()
        logger.info("Updated current prices for %d/%d stocks", updated, len(stocks))
        return updated
