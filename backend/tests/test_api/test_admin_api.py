"""Integration tests for admin API routes: auth, role enforcement, CRUD."""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from tests.conftest import create_test_admin, create_test_predictor, create_test_stock, create_test_user


def _auth_header(user_id: uuid.UUID, role: str = "admin") -> dict[str, str]:
    token = create_access_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}


# --- Auth enforcement ---


async def test_admin_route_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/admin/users")
    assert resp.status_code in (401, 403)  # No credentials → 401 or 403 depending on FastAPI version


async def test_admin_route_rejects_regular_user(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session, role="user")
    resp = await client.get("/api/v1/admin/users", headers=_auth_header(user.id, "user"))
    assert resp.status_code == 403


async def test_admin_route_allows_admin(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    resp = await client.get("/api/v1/admin/users", headers=_auth_header(admin.id, "admin"))
    assert resp.status_code == 200


# --- Predictor CRUD ---


async def test_create_predictor(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    resp = await client.post(
        "/api/v1/admin/predictors",
        json={"name": "New Analyst", "type": "individual"},
        headers=_auth_header(admin.id),
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "New Analyst"
    assert data["slug"] == "new-analyst"


async def test_update_predictor(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    predictor = await create_test_predictor(db_session, name="Old", slug="old")

    resp = await client.patch(
        f"/api/v1/admin/predictors/{predictor.id}",
        json={"name": "Updated"},
        headers=_auth_header(admin.id),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated"


# --- Stock CRUD ---


async def test_create_stock(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    resp = await client.post(
        "/api/v1/admin/stocks",
        json={"symbol": "NEWSTOCK", "name": "New Stock Ltd", "exchange": "NSE"},
        headers=_auth_header(admin.id),
    )
    assert resp.status_code == 201
    assert resp.json()["symbol"] == "NEWSTOCK"


# --- Review queue ---


async def test_review_queue_accessible_by_moderator(client: AsyncClient, db_session: AsyncSession) -> None:
    mod = await create_test_user(db_session, role="moderator")
    resp = await client.get("/api/v1/admin/review-queue", headers=_auth_header(mod.id, "moderator"))
    assert resp.status_code == 200


# --- Approve / Reject ---


async def test_approve_reject_flow(client: AsyncClient, db_session: AsyncSession) -> None:

    admin = await create_test_admin(db_session)
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    # Create a prediction via admin endpoint
    resp = await client.post(
        "/api/v1/admin/predictions",
        json={
            "predictor_id": str(predictor.id),
            "stock_id": str(stock.id),
            "target_price": "1500.00",
            "price_at_prediction": "1200.00",
            "prediction_date": "2025-01-15",
            "source_url": "https://example.com/article",
            "source_type": "news_article",
        },
        headers=_auth_header(admin.id),
    )
    assert resp.status_code == 201
    pred_id = resp.json()["id"]
    assert resp.json()["status"] == "pending_review"

    # Approve it
    resp = await client.post(
        f"/api/v1/admin/predictions/{pred_id}/approve",
        headers=_auth_header(admin.id),
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


# --- User management ---


async def test_change_user_role(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    user = await create_test_user(db_session, role="user")

    resp = await client.patch(
        f"/api/v1/admin/users/{user.id}/role",
        json={"role": "moderator"},
        headers=_auth_header(admin.id),
    )
    assert resp.status_code == 200
    assert resp.json()["role"] == "moderator"


async def test_ban_unban_user(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    user = await create_test_user(db_session)

    # Ban
    resp = await client.patch(
        f"/api/v1/admin/users/{user.id}/ban",
        json={"ban_reason": "Spam"},
        headers=_auth_header(admin.id),
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is False

    # Unban
    resp = await client.delete(
        f"/api/v1/admin/users/{user.id}/ban",
        headers=_auth_header(admin.id),
    )
    assert resp.status_code == 200
    assert resp.json()["is_active"] is True
