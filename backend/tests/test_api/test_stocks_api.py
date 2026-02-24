"""Integration tests for public stock API routes."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_stock


async def test_get_stock_by_symbol(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_test_stock(db_session, symbol="RELIANCE", name="Reliance Industries")

    resp = await client.get("/api/v1/stocks/RELIANCE")
    assert resp.status_code == 200
    data = resp.json()
    assert data["symbol"] == "RELIANCE"
    assert data["name"] == "Reliance Industries"


async def test_get_stock_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/stocks/NONEXIST")
    assert resp.status_code == 404


async def test_get_stock_predictions_empty(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_test_stock(db_session, symbol="EMPTY")

    resp = await client.get("/api/v1/stocks/EMPTY/predictions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["has_more"] is False
