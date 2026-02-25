"""Tests for StatsService — platform statistics aggregation."""

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scorecard import PredictorScorecard
from app.services.stats import StatsService
from tests.conftest import (
    create_test_outcome,
    create_test_prediction,
    create_test_predictor,
    create_test_stock,
)


async def test_empty_database(db_session: AsyncSession) -> None:
    """All counts zero, avg_accuracy None on empty DB."""
    service = StatsService(db_session)
    stats = await service.get_platform_stats()
    assert stats.total_predictions == 0
    assert stats.total_predictors == 0
    assert stats.total_stocks == 0
    assert stats.avg_accuracy_pct is None
    assert stats.total_evaluated == 0


async def test_counts_only_approved_predictions(db_session: AsyncSession) -> None:
    """Only approved predictions are counted."""
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id, status="approved")
    await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id, status="pending_review")
    await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id, status="rejected")

    service = StatsService(db_session)
    stats = await service.get_platform_stats()
    assert stats.total_predictions == 1


async def test_distinct_predictors(db_session: AsyncSession) -> None:
    """Counts distinct predictors with approved predictions."""
    p1 = await create_test_predictor(db_session, name="Analyst A")
    p2 = await create_test_predictor(db_session, name="Analyst B")
    stock = await create_test_stock(db_session)

    await create_test_prediction(db_session, predictor_id=p1.id, stock_id=stock.id)
    await create_test_prediction(db_session, predictor_id=p1.id, stock_id=stock.id)
    await create_test_prediction(db_session, predictor_id=p2.id, stock_id=stock.id)

    service = StatsService(db_session)
    stats = await service.get_platform_stats()
    assert stats.total_predictors == 2


async def test_distinct_stocks(db_session: AsyncSession) -> None:
    """Counts distinct stocks with approved predictions."""
    predictor = await create_test_predictor(db_session)
    s1 = await create_test_stock(db_session, symbol="AAAA")
    s2 = await create_test_stock(db_session, symbol="BBBB")

    await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=s1.id)
    await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=s1.id)
    await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=s2.id)

    service = StatsService(db_session)
    stats = await service.get_platform_stats()
    assert stats.total_stocks == 2


async def test_avg_accuracy_excludes_low_count(db_session: AsyncSession) -> None:
    """avg_accuracy_pct only includes scorecards with ≥10 total_predictions."""
    p1 = await create_test_predictor(db_session, name="High Count")
    p2 = await create_test_predictor(db_session, name="Low Count")

    sc1 = PredictorScorecard(predictor_id=p1.id, total_predictions=15, accuracy_pct=Decimal("80.00"))
    sc2 = PredictorScorecard(predictor_id=p2.id, total_predictions=5, accuracy_pct=Decimal("100.00"))
    db_session.add_all([sc1, sc2])
    await db_session.flush()

    service = StatsService(db_session)
    stats = await service.get_platform_stats()
    # Only sc1 qualifies (≥10 predictions), so avg = 80.00
    assert stats.avg_accuracy_pct is not None
    assert float(stats.avg_accuracy_pct) == 80.00


async def test_total_evaluated(db_session: AsyncSession) -> None:
    """Counts all prediction outcomes."""
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    pred1 = await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id)
    pred2 = await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id)

    await create_test_outcome(db_session, prediction_id=pred1.id, outcome_status="hit")
    await create_test_outcome(db_session, prediction_id=pred2.id, outcome_status="miss")

    service = StatsService(db_session)
    stats = await service.get_platform_stats()
    assert stats.total_evaluated == 2
