"""Tests for OutcomeRepository."""

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.outcome import OutcomeRepository
from tests.conftest import (
    create_test_outcome,
    create_test_prediction,
    create_test_predictor,
    create_test_stock,
)


async def test_get_by_prediction_id(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    prediction = await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id)
    outcome = await create_test_outcome(db_session, prediction_id=prediction.id)

    repo = OutcomeRepository(db_session)
    result = await repo.get_by_prediction_id(prediction.id)
    assert result is not None
    assert result.id == outcome.id


async def test_get_by_prediction_id_not_found(db_session: AsyncSession) -> None:
    import uuid

    repo = OutcomeRepository(db_session)
    result = await repo.get_by_prediction_id(uuid.uuid4())
    assert result is None


async def test_find_ready_for_evaluation(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    # Approved, eval date passed, no outcome → eligible
    p1 = await create_test_prediction(
        db_session,
        predictor_id=predictor.id,
        stock_id=stock.id,
        status="approved",
        default_eval_date=date(2025, 6, 1),
    )
    # Approved, eval date in future → not eligible
    await create_test_prediction(
        db_session,
        predictor_id=predictor.id,
        stock_id=stock.id,
        status="approved",
        default_eval_date=date(2099, 1, 1),
    )
    # Pending review → not eligible
    await create_test_prediction(
        db_session,
        predictor_id=predictor.id,
        stock_id=stock.id,
        status="pending_review",
        default_eval_date=date(2025, 6, 1),
    )
    # Already has outcome → not eligible
    p4 = await create_test_prediction(
        db_session,
        predictor_id=predictor.id,
        stock_id=stock.id,
        status="approved",
        default_eval_date=date(2025, 6, 1),
    )
    await create_test_outcome(db_session, prediction_id=p4.id)

    repo = OutcomeRepository(db_session)
    ready = await repo.find_ready_for_evaluation(date(2026, 1, 1))
    assert len(ready) == 1
    assert ready[0].id == p1.id


async def test_count_by_status_for_predictor(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    p1 = await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id)
    p2 = await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id)
    p3 = await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id)

    await create_test_outcome(db_session, prediction_id=p1.id, outcome_status="hit")
    await create_test_outcome(db_session, prediction_id=p2.id, outcome_status="miss")
    await create_test_outcome(db_session, prediction_id=p3.id, outcome_status="partial_hit")

    repo = OutcomeRepository(db_session)
    counts = await repo.count_by_status_for_predictor(predictor.id)
    assert counts["hit"] == 1
    assert counts["miss"] == 1
    assert counts["partial_hit"] == 1


async def test_list_by_predictor(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    p1 = await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id)
    p2 = await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id)
    await create_test_outcome(db_session, prediction_id=p1.id)
    await create_test_outcome(db_session, prediction_id=p2.id)

    repo = OutcomeRepository(db_session)
    outcomes = await repo.list_by_predictor(predictor.id)
    assert len(outcomes) == 2


async def test_list_by_stock(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    p1 = await create_test_prediction(db_session, predictor_id=predictor.id, stock_id=stock.id)
    await create_test_outcome(db_session, prediction_id=p1.id)

    repo = OutcomeRepository(db_session)
    outcomes = await repo.list_by_stock(stock.id)
    assert len(outcomes) == 1
