"""Integration tests for following API routes."""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from tests.conftest import create_test_predictor, create_test_user


def _auth_header(user_id: uuid.UUID, role: str = "user") -> dict[str, str]:
    token = create_access_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}


async def test_follow_predictor(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)

    resp = await client.post(
        "/api/v1/following",
        json={"predictor_id": str(predictor.id)},
        headers=_auth_header(user.id),
    )
    assert resp.status_code == 201


async def test_follow_duplicate_returns_409(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    headers = _auth_header(user.id)

    await client.post("/api/v1/following", json={"predictor_id": str(predictor.id)}, headers=headers)
    resp = await client.post("/api/v1/following", json={"predictor_id": str(predictor.id)}, headers=headers)
    assert resp.status_code == 409


async def test_follow_nonexistent_returns_404(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)

    resp = await client.post(
        "/api/v1/following",
        json={"predictor_id": str(uuid.uuid4())},
        headers=_auth_header(user.id),
    )
    assert resp.status_code == 404


async def test_unfollow(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    headers = _auth_header(user.id)

    await client.post("/api/v1/following", json={"predictor_id": str(predictor.id)}, headers=headers)
    resp = await client.delete(f"/api/v1/following/{predictor.id}", headers=headers)
    assert resp.status_code == 204


async def test_unfollow_not_following_returns_404(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)

    resp = await client.delete(f"/api/v1/following/{uuid.uuid4()}", headers=_auth_header(user.id))
    assert resp.status_code == 404


async def test_list_following(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    headers = _auth_header(user.id)

    await client.post("/api/v1/following", json={"predictor_id": str(predictor.id)}, headers=headers)
    resp = await client.get("/api/v1/following", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["predictor_name"] == predictor.name


async def test_check_following(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    headers = _auth_header(user.id)

    resp = await client.get(f"/api/v1/following/check/{predictor.id}", headers=headers)
    assert resp.json()["following"] is False

    await client.post("/api/v1/following", json={"predictor_id": str(predictor.id)}, headers=headers)
    resp = await client.get(f"/api/v1/following/check/{predictor.id}", headers=headers)
    assert resp.json()["following"] is True


async def test_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/following")
    assert resp.status_code in (401, 403)


async def test_list_empty_following(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    resp = await client.get("/api/v1/following", headers=_auth_header(user.id))
    assert resp.status_code == 200
    assert resp.json()["items"] == []
