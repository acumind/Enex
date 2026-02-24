"""Tests for yfinance adapter — symbol conversion and mock data fetching."""

from datetime import date
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from app.integrations.price_data.yfinance_adapter import (
    YFinanceAdapter,
    _from_yf_symbol,
    _to_yf_symbol,
)

# ---------------------------------------------------------------------------
# Symbol conversion
# ---------------------------------------------------------------------------


def test_to_yf_symbol_plain() -> None:
    assert _to_yf_symbol("RELIANCE") == "RELIANCE.NS"


def test_to_yf_symbol_already_ns() -> None:
    assert _to_yf_symbol("RELIANCE.NS") == "RELIANCE.NS"


def test_to_yf_symbol_already_bo() -> None:
    assert _to_yf_symbol("RELIANCE.BO") == "RELIANCE.BO"


def test_from_yf_symbol_ns() -> None:
    assert _from_yf_symbol("RELIANCE.NS") == "RELIANCE"


def test_from_yf_symbol_bo() -> None:
    assert _from_yf_symbol("RELIANCE.BO") == "RELIANCE"


def test_from_yf_symbol_plain() -> None:
    assert _from_yf_symbol("RELIANCE") == "RELIANCE"


# ---------------------------------------------------------------------------
# fetch_historical
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Create a sample DataFrame mimicking yfinance output."""
    idx = pd.DatetimeIndex([pd.Timestamp("2025-01-15"), pd.Timestamp("2025-01-16")])
    return pd.DataFrame(
        {
            "Open": [1190.0, 1210.0],
            "High": [1220.0, 1250.0],
            "Low": [1180.0, 1200.0],
            "Close": [1210.0, 1240.0],
            "Adj Close": [1208.0, 1238.0],
            "Volume": [1000000, 1200000],
        },
        index=idx,
    )


async def test_fetch_historical_success(sample_df: pd.DataFrame) -> None:
    adapter = YFinanceAdapter()
    with patch("app.integrations.price_data.yfinance_adapter.yf.download", return_value=sample_df):
        prices = await adapter.fetch_historical("RELIANCE", date(2025, 1, 15), date(2025, 1, 16))

    assert len(prices) == 2
    assert prices[0].trade_date == date(2025, 1, 15)
    assert prices[0].close_price == Decimal("1210.0")
    assert prices[0].adjusted_close == Decimal("1208.0")
    assert prices[0].volume == 1000000
    assert prices[1].trade_date == date(2025, 1, 16)


async def test_fetch_historical_empty() -> None:
    adapter = YFinanceAdapter()
    with patch(
        "app.integrations.price_data.yfinance_adapter.yf.download",
        return_value=pd.DataFrame(),
    ):
        prices = await adapter.fetch_historical("RELIANCE", date(2025, 1, 15), date(2025, 1, 16))

    assert prices == []


async def test_fetch_historical_exception() -> None:
    adapter = YFinanceAdapter()
    with patch(
        "app.integrations.price_data.yfinance_adapter.yf.download",
        side_effect=Exception("Network error"),
    ):
        prices = await adapter.fetch_historical("RELIANCE", date(2025, 1, 15), date(2025, 1, 16))

    assert prices == []


async def test_fetch_historical_malformed_row() -> None:
    """Rows with NaN close price should be skipped."""
    idx = pd.DatetimeIndex([pd.Timestamp("2025-01-15")])
    df = pd.DataFrame(
        {
            "Open": [float("nan")],
            "High": [float("nan")],
            "Low": [float("nan")],
            "Close": [float("nan")],
            "Adj Close": [float("nan")],
            "Volume": [0],
        },
        index=idx,
    )
    adapter = YFinanceAdapter()
    with patch("app.integrations.price_data.yfinance_adapter.yf.download", return_value=df):
        prices = await adapter.fetch_historical("RELIANCE", date(2025, 1, 15), date(2025, 1, 15))

    assert prices == []


# ---------------------------------------------------------------------------
# fetch_current_prices
# ---------------------------------------------------------------------------


async def test_fetch_current_prices_success() -> None:
    adapter = YFinanceAdapter()

    mock_ticker = MagicMock()
    mock_ticker.info = {"currentPrice": 1500.50}

    mock_tickers = MagicMock()
    mock_tickers.tickers = {"RELIANCE.NS": mock_ticker}

    with patch("app.integrations.price_data.yfinance_adapter.yf.Tickers", return_value=mock_tickers):
        result = await adapter.fetch_current_prices(["RELIANCE"])

    assert result == {"RELIANCE": Decimal("1500.5")}


async def test_fetch_current_prices_empty_input() -> None:
    adapter = YFinanceAdapter()
    result = await adapter.fetch_current_prices([])
    assert result == {}


async def test_fetch_current_prices_exception() -> None:
    adapter = YFinanceAdapter()
    with patch(
        "app.integrations.price_data.yfinance_adapter.yf.Tickers",
        side_effect=Exception("API error"),
    ):
        result = await adapter.fetch_current_prices(["RELIANCE"])

    assert result == {}


async def test_fetch_current_prices_missing_ticker() -> None:
    adapter = YFinanceAdapter()

    mock_tickers = MagicMock()
    mock_tickers.tickers = {}  # No tickers returned

    with patch("app.integrations.price_data.yfinance_adapter.yf.Tickers", return_value=mock_tickers):
        result = await adapter.fetch_current_prices(["UNKNOWN"])

    assert result == {}
