"""Tests for ExtractionService — mock adapter + fetcher."""

from unittest.mock import AsyncMock, patch

from app.schemas.extraction import ExtractionResult
from app.services.extraction import ExtractionService


async def test_extract_from_url_success() -> None:
    mock_result = ExtractionResult(
        predictor_name="Test Analyst",
        stock_name="Test Corp",
        stock_symbol="TEST",
        target_price=1500.0,
        direction="buy",
        confidence=0.9,
        source_type="news_article",
    )

    service = ExtractionService()

    with (
        patch.object(service.fetcher, "fetch", new_callable=AsyncMock) as mock_fetch,
        patch.object(service.adapter, "extract_predictions", new_callable=AsyncMock) as mock_extract,
    ):
        mock_fetch.return_value = ("Article text about stock predictions", 5000)
        mock_extract.return_value = [mock_result]

        result = await service.extract_from_url("https://example.com/article")

    assert result.url == "https://example.com/article"
    assert len(result.predictions) == 1
    assert result.predictions[0].predictor_name == "Test Analyst"
    assert result.source_text_length == 5000
    mock_fetch.assert_awaited_once_with("https://example.com/article")
    mock_extract.assert_awaited_once()


async def test_extract_from_url_no_predictions() -> None:
    service = ExtractionService()

    with (
        patch.object(service.fetcher, "fetch", new_callable=AsyncMock) as mock_fetch,
        patch.object(service.adapter, "extract_predictions", new_callable=AsyncMock) as mock_extract,
    ):
        mock_fetch.return_value = ("Some article with no predictions", 2000)
        mock_extract.return_value = []

        result = await service.extract_from_url("https://example.com/no-predictions")

    assert result.predictions == []
    assert result.source_text_length == 2000
