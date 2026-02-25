"""Integration tests for watchlist API routes."""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from tests.conftest import create_test_stock, create_test_user


def _auth_header(user_id: uuid.UUID, role: str = "user") -> dict[str, str]:
    token = create_access_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}


async def test_add_to_watchlist(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock = await create_test_stock(db_session)

    resp = await client.post(
        "/api/v1/watchlist",
        json={"stock_id": str(stock.id)},
        headers=_auth_header(user.id),
    )
    assert resp.status_code == 201


async def test_add_duplicate_returns_409(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock = await create_test_stock(db_session)
    headers = _auth_header(user.id)

    await client.post("/api/v1/watchlist", json={"stock_id": str(stock.id)}, headers=headers)
    resp = await client.post("/api/v1/watchlist", json={"stock_id": str(stock.id)}, headers=headers)
    assert resp.status_code == 409


async def test_add_nonexistent_stock_returns_404(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)

    resp = await client.post(
        "/api/v1/watchlist",
        json={"stock_id": str(uuid.uuid4())},
        headers=_auth_header(user.id),
    )
    assert resp.status_code == 404


async def test_remove_from_watchlist(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock = await create_test_stock(db_session)
    headers = _auth_header(user.id)

    await client.post("/api/v1/watchlist", json={"stock_id": str(stock.id)}, headers=headers)
    resp = await client.delete(f"/api/v1/watchlist/{stock.id}", headers=headers)
    assert resp.status_code == 204


async def test_remove_not_watching_returns_404(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)

    resp = await client.delete(f"/api/v1/watchlist/{uuid.uuid4()}", headers=_auth_header(user.id))
    assert resp.status_code == 404


async def test_list_watchlist(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock = await create_test_stock(db_session)
    headers = _auth_header(user.id)

    await client.post("/api/v1/watchlist", json={"stock_id": str(stock.id)}, headers=headers)
    resp = await client.get("/api/v1/watchlist", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["stock_symbol"] == stock.symbol


async def test_check_watching(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    stock = await create_test_stock(db_session)
    headers = _auth_header(user.id)

    resp = await client.get(f"/api/v1/watchlist/check/{stock.id}", headers=headers)
    assert resp.json()["watching"] is False

    await client.post("/api/v1/watchlist", json={"stock_id": str(stock.id)}, headers=headers)
    resp = await client.get(f"/api/v1/watchlist/check/{stock.id}", headers=headers)
    assert resp.json()["watching"] is True


async def test_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/watchlist")
    assert resp.status_code in (401, 403)


async def test_list_empty_watchlist(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    resp = await client.get("/api/v1/watchlist", headers=_auth_header(user.id))
    assert resp.status_code == 200
    assert resp.json()["items"] == []
