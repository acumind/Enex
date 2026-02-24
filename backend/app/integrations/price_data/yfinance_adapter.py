"""yfinance adapter — fetches Indian stock price data via Yahoo Finance."""

import asyncio
import logging
from datetime import date, timedelta
from decimal import Decimal

import yfinance as yf

from app.integrations.price_data.protocol import DailyPrice

logger = logging.getLogger(__name__)


def _to_yf_symbol(symbol: str) -> str:
    """Convert NSE symbol to yfinance format (append .NS)."""
    if symbol.endswith(".NS") or symbol.endswith(".BO"):
        return symbol
    return f"{symbol}.NS"


def _from_yf_symbol(yf_symbol: str) -> str:
    """Convert yfinance symbol back to plain NSE symbol."""
    for suffix in (".NS", ".BO"):
        if yf_symbol.endswith(suffix):
            return yf_symbol[: -len(suffix)]
    return yf_symbol


class YFinanceAdapter:
    async def fetch_historical(self, symbol: str, start_date: date, end_date: date) -> list[DailyPrice]:
        yf_symbol = _to_yf_symbol(symbol)
        # yfinance end date is exclusive, so add 1 day
        end_exclusive = end_date + timedelta(days=1)

        try:
            df = await asyncio.to_thread(
                yf.download,
                yf_symbol,
                start=start_date.isoformat(),
                end=end_exclusive.isoformat(),
                auto_adjust=False,
                progress=False,
            )
        except Exception:
            logger.exception("yfinance download failed for %s", yf_symbol)
            return []

        if df is None or df.empty:
            return []

        prices: list[DailyPrice] = []
        for idx, row in df.iterrows():
            try:
                trade_date = idx.date() if hasattr(idx, "date") else idx
                close_val = row.get("Close")
                if close_val is None or (hasattr(close_val, "__iter__") and not isinstance(close_val, str)):
                    # Multi-ticker DataFrame — extract scalar
                    close_val = row["Close"].iloc[0] if hasattr(row["Close"], "iloc") else row["Close"]
                if close_val is None or str(close_val) == "nan":
                    continue
                prices.append(
                    DailyPrice(
                        trade_date=trade_date,
                        open_price=_safe_decimal(row.get("Open")),
                        high_price=_safe_decimal(row.get("High")),
                        low_price=_safe_decimal(row.get("Low")),
                        close_price=Decimal(str(round(float(close_val), 2))),
                        volume=_safe_int(row.get("Volume")),
                        adjusted_close=_safe_decimal(row.get("Adj Close")),
                    )
                )
            except Exception:
                logger.warning("Skipping malformed row for %s at %s", yf_symbol, idx)
                continue

        return prices

    async def fetch_current_prices(self, symbols: list[str]) -> dict[str, Decimal]:
        if not symbols:
            return {}

        yf_symbols = [_to_yf_symbol(s) for s in symbols]
        yf_string = " ".join(yf_symbols)

        try:
            tickers = await asyncio.to_thread(yf.Tickers, yf_string)
        except Exception:
            logger.exception("yfinance Tickers failed for %s", yf_string)
            return {}

        results: dict[str, Decimal] = {}
        for yf_sym, original_sym in zip(yf_symbols, symbols, strict=True):
            try:
                ticker = tickers.tickers.get(yf_sym)
                if ticker is None:
                    continue
                info = ticker.info or {}
                price = info.get("currentPrice") or info.get("regularMarketPrice")
                if price is not None:
                    results[original_sym] = Decimal(str(round(float(price), 2)))
            except Exception:
                logger.warning("Failed to get current price for %s", yf_sym)
                continue

        return results


def _safe_decimal(val: object) -> Decimal | None:
    if val is None:
        return None
    try:
        f = float(val)
        if str(f) == "nan":
            return None
        return Decimal(str(round(f, 2)))
    except (TypeError, ValueError):
        return None


def _safe_int(val: object) -> int | None:
    if val is None:
        return None
    try:
        f = float(val)
        if str(f) == "nan":
            return None
        return int(f)
    except (TypeError, ValueError):
        return None
