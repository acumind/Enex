"""Integration tests for search API route."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_predictor, create_test_stock


async def test_search_returns_matching_predictors(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_test_predictor(db_session, name="Rakesh Jhunjhunwala", slug="rakesh-jhunjhunwala")

    resp = await client.get("/api/v1/search?q=Rakesh")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["predictors"]) == 1
    assert data["predictors"][0]["name"] == "Rakesh Jhunjhunwala"
    assert data["predictors"][0]["type"] == "predictor"


async def test_search_returns_matching_stocks(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_test_stock(db_session, symbol="RELIANCE", name="Reliance Industries")

    resp = await client.get("/api/v1/search?q=reliance")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["stocks"]) == 1
    assert data["stocks"][0]["slug_or_symbol"] == "RELIANCE"


async def test_search_returns_both(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_test_predictor(db_session, name="HDFC Analyst", slug="hdfc-analyst")
    await create_test_stock(db_session, symbol="HDFC", name="HDFC Bank Ltd")

    resp = await client.get("/api/v1/search?q=HDFC")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["predictors"]) >= 1
    assert len(data["stocks"]) >= 1


async def test_search_empty_query_returns_422(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/search?q=")
    assert resp.status_code == 422


async def test_search_no_match(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/search?q=zzzznonexistent")
    assert resp.status_code == 200
    data = resp.json()
    assert data["predictors"] == []
    assert data["stocks"] == []


async def test_search_respects_limit(client: AsyncClient, db_session: AsyncSession) -> None:
    for i in range(5):
        await create_test_predictor(db_session, name=f"Analyst {i}", slug=f"analyst-{i}")

    resp = await client.get("/api/v1/search?q=Analyst&limit=2")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["predictors"]) == 2
