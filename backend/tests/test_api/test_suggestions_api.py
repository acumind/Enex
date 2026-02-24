"""Integration tests for suggestion API routes — user suggest, admin list/promote/dismiss."""

import uuid
from unittest.mock import patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from tests.conftest import create_test_admin, create_test_user


def _auth_header(user_id: uuid.UUID, role: str = "user") -> dict[str, str]:
    token = create_access_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}


async def test_suggest_prediction(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    resp = await client.post(
        "/api/v1/predictions/suggest",
        json={"url": "https://example.com/article", "note": "Good call"},
        headers=_auth_header(user.id),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["url"] == "https://example.com/article"
    assert data["status"] == "pending"


async def test_suggest_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/predictions/suggest",
        json={"url": "https://example.com/article"},
    )
    assert resp.status_code in (401, 403)


async def test_admin_list_suggestions(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    admin = await create_test_admin(db_session)

    # Create a suggestion
    await client.post(
        "/api/v1/predictions/suggest",
        json={"url": "https://example.com/article"},
        headers=_auth_header(user.id),
    )

    resp = await client.get(
        "/api/v1/admin/suggestions",
        headers=_auth_header(admin.id, "admin"),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1


async def test_admin_dismiss_suggestion(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    admin = await create_test_admin(db_session)

    # Create a suggestion
    resp = await client.post(
        "/api/v1/predictions/suggest",
        json={"url": "https://example.com/dismiss-me"},
        headers=_auth_header(user.id),
    )
    suggestion_id = resp.json()["id"]

    # Dismiss it
    resp = await client.post(
        f"/api/v1/admin/suggestions/{suggestion_id}/dismiss",
        headers=_auth_header(admin.id, "admin"),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "dismissed"


async def test_admin_promote_suggestion(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    admin = await create_test_admin(db_session)

    # Create a suggestion
    resp = await client.post(
        "/api/v1/predictions/suggest",
        json={"url": "https://example.com/promote-me"},
        headers=_auth_header(user.id),
    )
    suggestion_id = resp.json()["id"]

    # Promote it (mock celery task)
    with patch("app.jobs.extraction.extract_prediction_task") as mock_task:
        mock_task.delay.return_value = None
        resp = await client.post(
            f"/api/v1/admin/suggestions/{suggestion_id}/promote",
            headers=_auth_header(admin.id, "admin"),
        )

    assert resp.status_code == 200
    assert resp.json()["status"] == "promoted"


async def test_regular_user_cannot_list_suggestions(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session, role="user")
    resp = await client.get(
        "/api/v1/admin/suggestions",
        headers=_auth_header(user.id, "user"),
    )
    assert resp.status_code == 403
