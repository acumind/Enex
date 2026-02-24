"""Tests for price fetcher background job."""

from unittest.mock import AsyncMock, patch

import pytest

# Patch targets (lazy imports inside _run_price_fetch)
_P_SESSION_FACTORY = "app.core.database.async_session_factory"
_P_PRICE_FETCHER_SVC = "app.services.price_fetcher.PriceFetcherService"


def _make_session_ctx(mock_session):  # type: ignore[no-untyped-def]
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return mock_ctx


async def test_run_price_fetch_calls_service() -> None:
    from app.jobs.price_fetcher import _run_price_fetch

    mock_session = AsyncMock()
    mock_service = AsyncMock()
    mock_service.fetch_all_active_stocks.return_value = 100
    mock_service.update_current_prices.return_value = 50

    with (
        patch(_P_SESSION_FACTORY, return_value=_make_session_ctx(mock_session)),
        patch(_P_PRICE_FETCHER_SVC, return_value=mock_service),
    ):
        result = await _run_price_fetch()

    assert result == {"prices_upserted": 100, "current_prices_updated": 50}
    mock_service.fetch_all_active_stocks.assert_awaited_once()
    mock_service.update_current_prices.assert_awaited_once()
    mock_session.commit.assert_awaited_once()


def test_fetch_daily_prices_task_success() -> None:
    with patch("app.jobs.price_fetcher.asyncio.run", return_value={"prices_upserted": 10, "current_prices_updated": 5}):
        from app.jobs.price_fetcher import fetch_daily_prices_task

        result = fetch_daily_prices_task()
    assert result["prices_upserted"] == 10


def test_fetch_daily_prices_task_retries_on_failure() -> None:
    with patch("app.jobs.price_fetcher.asyncio.run", side_effect=RuntimeError("boom")):
        from app.jobs.price_fetcher import fetch_daily_prices_task

        with pytest.raises(RuntimeError, match="boom"):
            fetch_daily_prices_task()
