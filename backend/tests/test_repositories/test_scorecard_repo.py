"""Tests for ScorecardRepository."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.scorecard import ScorecardRepository
from tests.conftest import create_test_predictor


async def test_upsert_insert(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)

    repo = ScorecardRepository(db_session)
    scorecard = await repo.upsert(
        {
            "predictor_id": predictor.id,
            "total_predictions": 20,
            "hits": 10,
            "misses": 5,
            "partial_hits": 3,
            "pending": 2,
            "accuracy_pct": Decimal("67.50"),
            "avg_deviation_pct": Decimal("-2.50"),
            "avg_upside_predicted": Decimal("15.00"),
            "sector_accuracy": {"Technology": 80.0, "Banking": 60.0},
            "best_sector": "Technology",
            "worst_sector": "Banking",
            "streak_current": 3,
            "last_prediction_date": date(2025, 6, 1),
            "last_updated": datetime(2025, 6, 15),
        }
    )
    assert scorecard.predictor_id == predictor.id
    assert scorecard.total_predictions == 20
    assert scorecard.accuracy_pct == Decimal("67.50")


async def test_upsert_update(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)

    repo = ScorecardRepository(db_session)
    await repo.upsert(
        {
            "predictor_id": predictor.id,
            "total_predictions": 10,
            "hits": 5,
            "misses": 3,
            "partial_hits": 2,
            "pending": 0,
            "accuracy_pct": Decimal("60.00"),
            "sector_accuracy": {},
            "streak_current": 0,
            "last_updated": datetime(2025, 6, 1),
        }
    )

    # Update with new data
    updated = await repo.upsert(
        {
            "predictor_id": predictor.id,
            "total_predictions": 15,
            "hits": 8,
            "misses": 4,
            "partial_hits": 3,
            "pending": 0,
            "accuracy_pct": Decimal("63.33"),
            "sector_accuracy": {"Technology": 75.0},
            "streak_current": 2,
            "last_updated": datetime(2025, 7, 1),
        }
    )
    assert updated.total_predictions == 15
    assert updated.accuracy_pct == Decimal("63.33")


async def test_get_by_predictor_id(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)

    repo = ScorecardRepository(db_session)
    await repo.upsert(
        {
            "predictor_id": predictor.id,
            "total_predictions": 10,
            "hits": 5,
            "misses": 3,
            "partial_hits": 2,
            "pending": 0,
            "accuracy_pct": Decimal("60.00"),
            "sector_accuracy": {},
            "streak_current": 0,
            "last_updated": datetime(2025, 6, 1),
        }
    )

    result = await repo.get_by_predictor_id(predictor.id)
    assert result is not None
    assert result.total_predictions == 10


async def test_get_leaderboard(db_session: AsyncSession) -> None:
    p1 = await create_test_predictor(db_session, name="Top Analyst")
    p2 = await create_test_predictor(db_session, name="Mid Analyst")
    p3 = await create_test_predictor(db_session, name="Low Analyst")

    repo = ScorecardRepository(db_session)
    now = datetime(2025, 6, 1)

    await repo.upsert(
        {
            "predictor_id": p1.id,
            "total_predictions": 20,
            "hits": 15,
            "misses": 3,
            "partial_hits": 2,
            "pending": 0,
            "accuracy_pct": Decimal("80.00"),
            "sector_accuracy": {},
            "streak_current": 5,
            "last_updated": now,
        }
    )
    await repo.upsert(
        {
            "predictor_id": p2.id,
            "total_predictions": 15,
            "hits": 8,
            "misses": 5,
            "partial_hits": 2,
            "pending": 0,
            "accuracy_pct": Decimal("60.00"),
            "sector_accuracy": {},
            "streak_current": 1,
            "last_updated": now,
        }
    )
    # Below min_predictions threshold
    await repo.upsert(
        {
            "predictor_id": p3.id,
            "total_predictions": 5,
            "hits": 3,
            "misses": 1,
            "partial_hits": 1,
            "pending": 0,
            "accuracy_pct": Decimal("70.00"),
            "sector_accuracy": {},
            "streak_current": 0,
            "last_updated": now,
        }
    )

    rows = await repo.get_leaderboard(min_predictions=10, limit=50, offset=0)
    assert len(rows) == 2
    # Sorted by accuracy desc
    scorecard_0, predictor_0 = rows[0]
    assert predictor_0.name == "Top Analyst"
    assert scorecard_0.accuracy_pct == Decimal("80.00")

    scorecard_1, predictor_1 = rows[1]
    assert predictor_1.name == "Mid Analyst"


async def test_get_leaderboard_offset(db_session: AsyncSession) -> None:
    p1 = await create_test_predictor(db_session, name="A")
    p2 = await create_test_predictor(db_session, name="B")

    repo = ScorecardRepository(db_session)
    now = datetime(2025, 6, 1)
    for p, acc in [(p1, "80.00"), (p2, "60.00")]:
        await repo.upsert(
            {
                "predictor_id": p.id,
                "total_predictions": 20,
                "hits": 10,
                "misses": 5,
                "partial_hits": 5,
                "pending": 0,
                "accuracy_pct": Decimal(acc),
                "sector_accuracy": {},
                "streak_current": 0,
                "last_updated": now,
            }
        )

    rows = await repo.get_leaderboard(min_predictions=10, limit=1, offset=1)
    assert len(rows) == 1
    _, predictor = rows[0]
    assert predictor.name == "B"
