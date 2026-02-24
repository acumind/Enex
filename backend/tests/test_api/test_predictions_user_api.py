"""Integration tests for user prediction routes — submit, list mine, duplicate detection."""

import uuid
from unittest.mock import patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from tests.conftest import create_test_predictor, create_test_stock, create_test_user


def _auth_header(user_id: uuid.UUID, role: str = "user") -> dict[str, str]:
    token = create_access_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}


def _prediction_payload(predictor_id: uuid.UUID, stock_id: uuid.UUID, **overrides) -> dict:  # type: ignore[type-arg]
    data = {
        "predictor_id": str(predictor_id),
        "stock_id": str(stock_id),
        "target_price": "1500.00",
        "price_at_prediction": "1200.00",
        "prediction_date": "2025-01-15",
        "source_url": "https://example.com/article",
        "source_type": "news_article",
    }
    data.update(overrides)
    return data


async def test_submit_prediction(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    with patch("app.jobs.archive.archive_url_task"):
        resp = await client.post(
            "/api/v1/predictions",
            json=_prediction_payload(predictor.id, stock.id),
            headers=_auth_header(user.id),
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending_review"
    assert data["submitted_by"] == str(user.id)


async def test_submit_requires_auth(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/predictions",
        json={"predictor_id": str(uuid.uuid4()), "stock_id": str(uuid.uuid4())},
    )
    assert resp.status_code in (401, 403)


async def test_submit_with_extraction_metadata(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    payload = _prediction_payload(
        predictor.id,
        stock.id,
        extraction_method="ai_assisted",
        ai_confidence="0.85",
    )

    with patch("app.jobs.archive.archive_url_task"):
        resp = await client.post(
            "/api/v1/predictions",
            json=payload,
            headers=_auth_header(user.id),
        )

    assert resp.status_code == 201
    data = resp.json()
    assert data["extraction_method"] == "ai_assisted"


async def test_duplicate_detection_returns_409(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    payload = _prediction_payload(predictor.id, stock.id)

    with patch("app.jobs.archive.archive_url_task"):
        resp1 = await client.post(
            "/api/v1/predictions",
            json=payload,
            headers=_auth_header(user.id),
        )
    assert resp1.status_code == 201

    with patch("app.jobs.archive.archive_url_task"):
        resp2 = await client.post(
            "/api/v1/predictions",
            json=payload,
            headers=_auth_header(user.id),
        )
    assert resp2.status_code == 409


async def test_list_my_predictions(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    with patch("app.jobs.archive.archive_url_task"):
        await client.post(
            "/api/v1/predictions",
            json=_prediction_payload(predictor.id, stock.id),
            headers=_auth_header(user.id),
        )

    resp = await client.get(
        "/api/v1/predictions/mine",
        headers=_auth_header(user.id),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["submitted_by"] == str(user.id)


async def test_list_mine_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/predictions/mine")
    assert resp.status_code in (401, 403)
