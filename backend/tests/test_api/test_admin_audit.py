"""Integration tests for admin audit log and new admin endpoints."""

import uuid

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from tests.conftest import (
    create_test_admin,
    create_test_prediction,
    create_test_predictor,
    create_test_stock,
    create_test_user,
)


def _auth_header(user_id: uuid.UUID, role: str = "admin") -> dict[str, str]:
    token = create_access_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}


# --- Admin Stats ---


async def test_get_admin_stats(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    resp = await client.get("/api/v1/admin/stats", headers=_auth_header(admin.id))
    assert resp.status_code == 200
    data = resp.json()
    assert "pending_predictions" in data
    assert "pending_suggestions" in data
    assert "total_users" in data
    assert "total_predictors" in data
    assert "total_stocks" in data
    assert "predictions_today" in data
    assert "predictions_this_week" in data


async def test_admin_stats_requires_admin(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session, role="user")
    resp = await client.get("/api/v1/admin/stats", headers=_auth_header(user.id, "user"))
    assert resp.status_code == 403


# --- Audit Log ---


async def test_audit_log_records_on_create_predictor(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    headers = _auth_header(admin.id)

    # Create a predictor (triggers audit)
    resp = await client.post(
        "/api/v1/admin/predictors",
        json={"name": "Audit Test Analyst", "type": "individual"},
        headers=headers,
    )
    assert resp.status_code == 201

    # Check audit log
    resp = await client.get("/api/v1/admin/audit-log", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) >= 1
    assert data["items"][0]["action"] == "predictor.create"
    assert data["items"][0]["entity_type"] == "predictor"


async def test_audit_log_pagination(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    headers = _auth_header(admin.id)

    # Create several audit entries via stock creation
    for i in range(5):
        await client.post(
            "/api/v1/admin/stocks",
            json={"symbol": f"AUD{i:02d}", "name": f"Audit Stock {i}", "exchange": "NSE"},
            headers=headers,
        )

    resp = await client.get("/api/v1/admin/audit-log?limit=3", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 3
    assert data["has_more"] is True


# --- Prediction Edit ---


async def test_edit_prediction(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    prediction = await create_test_prediction(
        db_session,
        predictor_id=predictor.id,
        stock_id=stock.id,
        status="pending_review",
    )
    await db_session.commit()

    resp = await client.patch(
        f"/api/v1/admin/predictions/{prediction.id}",
        json={"target_price": "2000.00"},
        headers=_auth_header(admin.id),
    )
    assert resp.status_code == 200
    assert resp.json()["target_price"] == "2000.00"


async def test_edit_evaluated_prediction_blocked(client: AsyncClient, db_session: AsyncSession) -> None:
    from tests.conftest import create_test_outcome

    admin = await create_test_admin(db_session)
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    prediction = await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id)
    await create_test_outcome(db_session, prediction_id=prediction.id)
    await db_session.commit()

    resp = await client.patch(
        f"/api/v1/admin/predictions/{prediction.id}",
        json={"target_price": "2000.00"},
        headers=_auth_header(admin.id),
    )
    assert resp.status_code == 422  # BusinessRuleViolation


# --- Stock List/Update ---


async def test_list_stocks(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    await create_test_stock(db_session, symbol="LSTK1")
    await db_session.commit()

    resp = await client.get("/api/v1/admin/stocks", headers=_auth_header(admin.id))
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert len(data["items"]) >= 1


async def test_update_stock(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    stock = await create_test_stock(db_session, symbol="UPDSTK")
    await db_session.commit()

    resp = await client.patch(
        f"/api/v1/admin/stocks/{stock.id}",
        json={"name": "Updated Stock Name"},
        headers=_auth_header(admin.id),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Stock Name"


# --- Job Status ---


async def test_recent_jobs_endpoint(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    resp = await client.get("/api/v1/admin/jobs/recent", headers=_auth_header(admin.id))
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
