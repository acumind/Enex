"""Integration tests for notification API routes."""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from tests.conftest import create_test_notification, create_test_user


def _auth_header(user_id: uuid.UUID, role: str = "user") -> dict[str, str]:
    token = create_access_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}


async def test_list_notifications(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    await create_test_notification(db_session, user_id=user.id)

    resp = await client.get("/api/v1/notifications", headers=_auth_header(user.id))
    assert resp.status_code == 200
    assert len(resp.json()["items"]) == 1


async def test_unread_count(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    await create_test_notification(db_session, user_id=user.id, is_read=False)
    await create_test_notification(db_session, user_id=user.id, is_read=True)

    resp = await client.get("/api/v1/notifications/unread-count", headers=_auth_header(user.id))
    assert resp.status_code == 200
    assert resp.json()["count"] == 1


async def test_mark_read(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    n = await create_test_notification(db_session, user_id=user.id, is_read=False)

    resp = await client.post(f"/api/v1/notifications/{n.id}/read", headers=_auth_header(user.id))
    assert resp.status_code == 204


async def test_mark_read_not_found(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    resp = await client.post(f"/api/v1/notifications/{uuid.uuid4()}/read", headers=_auth_header(user.id))
    assert resp.status_code == 404


async def test_mark_all_read(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    await create_test_notification(db_session, user_id=user.id, is_read=False)
    await create_test_notification(db_session, user_id=user.id, is_read=False)

    resp = await client.post("/api/v1/notifications/read-all", headers=_auth_header(user.id))
    assert resp.status_code == 204


async def test_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/notifications")
    assert resp.status_code in (401, 403)
