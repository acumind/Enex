"""Integration tests for public prediction API routes."""

from httpx import AsyncClient


async def test_get_recent_predictions_empty(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/predictions/recent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["has_more"] is False
