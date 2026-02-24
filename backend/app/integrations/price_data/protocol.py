"""Price data protocol — interface for swappable price data providers."""

from datetime import date
from decimal import Decimal
from typing import Protocol, runtime_checkable

from pydantic import BaseModel


class DailyPrice(BaseModel):
    trade_date: date
    open_price: Decimal | None = None
    high_price: Decimal | None = None
    low_price: Decimal | None = None
    close_price: Decimal
    volume: int | None = None
    adjusted_close: Decimal | None = None


@runtime_checkable
class PriceDataProtocol(Protocol):
    async def fetch_historical(self, symbol: str, start_date: date, end_date: date) -> list[DailyPrice]: ...

    async def fetch_current_prices(self, symbols: list[str]) -> dict[str, Decimal]: ...
