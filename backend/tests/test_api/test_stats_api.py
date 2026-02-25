"""Tests for GET /api/v1/stats endpoint."""

from httpx import AsyncClient


async def test_stats_returns_200(client: AsyncClient) -> None:
    """GET /stats returns 200 even with empty data."""
    resp = await client.get("/api/v1/stats")
    assert resp.status_code == 200


async def test_stats_response_structure(client: AsyncClient) -> None:
    """Response matches PlatformStatsResponse schema."""
    resp = await client.get("/api/v1/stats")
    data = resp.json()
    assert "total_predictions" in data
    assert "total_predictors" in data
    assert "total_stocks" in data
    assert "avg_accuracy_pct" in data
    assert "total_evaluated" in data
    assert isinstance(data["total_predictions"], int)
    assert isinstance(data["total_predictors"], int)
    assert isinstance(data["total_stocks"], int)
    assert isinstance(data["total_evaluated"], int)
