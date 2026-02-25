"""Integration tests for outcome, leaderboard, and scorecard API routes."""

import uuid
from datetime import datetime
from decimal import Decimal

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from tests.conftest import (
    create_test_admin,
    create_test_outcome,
    create_test_prediction,
    create_test_predictor,
    create_test_stock,
    create_test_user,
)


def _auth_header(user_id: uuid.UUID, role: str = "admin") -> dict[str, str]:
    token = create_access_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}


# --- GET /outcomes/{prediction_id} ---


async def test_get_outcome_success(client: AsyncClient, db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    prediction = await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id)
    await create_test_outcome(db_session, prediction_id=prediction.id, outcome_status="hit")

    resp = await client.get(f"/api/v1/outcomes/{prediction.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["prediction_id"] == str(prediction.id)
    assert data["outcome_status"] == "hit"


async def test_get_outcome_not_found(client: AsyncClient) -> None:
    resp = await client.get(f"/api/v1/outcomes/{uuid.uuid4()}")
    assert resp.status_code == 404


# --- GET /leaderboard ---


async def test_get_leaderboard_empty(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/leaderboard")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_leaderboard_with_data(client: AsyncClient, db_session: AsyncSession) -> None:
    from app.repositories.scorecard import ScorecardRepository

    predictor = await create_test_predictor(db_session, name="Star Analyst")
    repo = ScorecardRepository(db_session)
    await repo.upsert(
        {
            "predictor_id": predictor.id,
            "total_predictions": 20,
            "hits": 15,
            "misses": 3,
            "partial_hits": 2,
            "pending": 0,
            "accuracy_pct": Decimal("80.00"),
            "sector_accuracy": {},
            "streak_current": 5,
            "last_updated": datetime(2025, 6, 1),
        }
    )

    resp = await client.get("/api/v1/leaderboard?min_predictions=10")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["predictor_name"] == "Star Analyst"
    assert data[0]["accuracy_pct"] == "80.00"


async def test_get_leaderboard_min_predictions_filter(client: AsyncClient, db_session: AsyncSession) -> None:
    from app.repositories.scorecard import ScorecardRepository

    predictor = await create_test_predictor(db_session)
    repo = ScorecardRepository(db_session)
    await repo.upsert(
        {
            "predictor_id": predictor.id,
            "total_predictions": 5,
            "hits": 3,
            "misses": 1,
            "partial_hits": 1,
            "pending": 0,
            "accuracy_pct": Decimal("70.00"),
            "sector_accuracy": {},
            "streak_current": 0,
            "last_updated": datetime(2025, 6, 1),
        }
    )

    # Default min_predictions=10, so 5 predictions shouldn't appear
    resp = await client.get("/api/v1/leaderboard")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_leaderboard_filter_by_predictor_type(client: AsyncClient, db_session: AsyncSession) -> None:
    from app.repositories.scorecard import ScorecardRepository

    ind = await create_test_predictor(db_session, name="Individual Analyst", predictor_type="individual")
    brk = await create_test_predictor(db_session, name="Big Brokerage", predictor_type="brokerage")
    repo = ScorecardRepository(db_session)
    for p in [ind, brk]:
        await repo.upsert(
            {
                "predictor_id": p.id,
                "total_predictions": 20,
                "hits": 15,
                "misses": 3,
                "partial_hits": 2,
                "pending": 0,
                "accuracy_pct": Decimal("80.00"),
                "sector_accuracy": {},
                "streak_current": 5,
                "last_updated": datetime(2025, 6, 1),
            }
        )

    resp = await client.get("/api/v1/leaderboard?predictor_type=individual")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["predictor_type"] == "individual"


async def test_get_leaderboard_sort_by_total_predictions(client: AsyncClient, db_session: AsyncSession) -> None:
    from app.repositories.scorecard import ScorecardRepository

    p1 = await create_test_predictor(db_session, name="Few Preds")
    p2 = await create_test_predictor(db_session, name="Many Preds")
    repo = ScorecardRepository(db_session)
    await repo.upsert(
        {
            "predictor_id": p1.id,
            "total_predictions": 15,
            "hits": 10,
            "misses": 3,
            "partial_hits": 2,
            "pending": 0,
            "accuracy_pct": Decimal("90.00"),
            "sector_accuracy": {},
            "streak_current": 3,
            "last_updated": datetime(2025, 6, 1),
        }
    )
    await repo.upsert(
        {
            "predictor_id": p2.id,
            "total_predictions": 50,
            "hits": 30,
            "misses": 10,
            "partial_hits": 10,
            "pending": 0,
            "accuracy_pct": Decimal("70.00"),
            "sector_accuracy": {},
            "streak_current": 1,
            "last_updated": datetime(2025, 6, 1),
        }
    )

    resp = await client.get("/api/v1/leaderboard?sort_by=total_predictions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["predictor_name"] == "Many Preds"


# --- GET /scorecards/{predictor_id} ---


async def test_get_scorecard_success(client: AsyncClient, db_session: AsyncSession) -> None:
    from app.repositories.scorecard import ScorecardRepository

    predictor = await create_test_predictor(db_session)
    repo = ScorecardRepository(db_session)
    await repo.upsert(
        {
            "predictor_id": predictor.id,
            "total_predictions": 15,
            "hits": 10,
            "misses": 3,
            "partial_hits": 2,
            "pending": 0,
            "accuracy_pct": Decimal("73.33"),
            "sector_accuracy": {"Technology": 80.0},
            "streak_current": 2,
            "last_updated": datetime(2025, 6, 1),
        }
    )

    resp = await client.get(f"/api/v1/scorecards/{predictor.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["predictor_id"] == str(predictor.id)
    assert data["total_predictions"] == 15


async def test_get_scorecard_not_found(client: AsyncClient) -> None:
    resp = await client.get(f"/api/v1/scorecards/{uuid.uuid4()}")
    assert resp.status_code == 404


# --- POST /admin/trigger-evaluation ---


async def test_trigger_evaluation_requires_admin(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session, role="user")
    resp = await client.post(
        "/api/v1/admin/trigger-evaluation",
        headers=_auth_header(user.id, "user"),
    )
    assert resp.status_code == 403


async def test_trigger_evaluation_no_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/admin/trigger-evaluation")
    assert resp.status_code in (401, 403)


async def test_trigger_evaluation_admin_success(client: AsyncClient, db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    resp = await client.post(
        "/api/v1/admin/trigger-evaluation",
        headers=_auth_header(admin.id, "admin"),
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "message" in data
    assert "predictions_evaluated" in data
    assert "scorecards_updated" in data
