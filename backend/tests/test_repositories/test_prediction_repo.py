"""Tests for PredictionRepository CRUD and queries."""

import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction
from app.repositories.prediction import PredictionRepository
from tests.conftest import create_test_predictor, create_test_stock, create_test_user


async def _create_prediction(
    db_session: AsyncSession,
    predictor_id: uuid.UUID,
    stock_id: uuid.UUID,
    *,
    status: str = "pending_review",
    created_at: datetime | None = None,
) -> Prediction:
    prediction = Prediction(
        predictor_id=predictor_id,
        stock_id=stock_id,
        target_price=Decimal("1500.00"),
        price_at_prediction=Decimal("1200.00"),
        prediction_date=date(2025, 1, 15),
        default_eval_date=date(2026, 1, 15),
        source_url="https://example.com/article",
        source_type="news_article",
        status=status,
    )
    if created_at is not None:
        prediction.created_at = created_at  # type: ignore[assignment]
    db_session.add(prediction)
    await db_session.flush()
    return prediction


async def test_list_by_predictor(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    await _create_prediction(db_session, predictor.id, stock.id)
    await _create_prediction(db_session, predictor.id, stock.id)

    repo = PredictionRepository(db_session)
    predictions = await repo.list_by_predictor(predictor.id)
    assert len(predictions) == 2


async def test_list_by_stock(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    await _create_prediction(db_session, predictor.id, stock.id)

    repo = PredictionRepository(db_session)
    predictions = await repo.list_by_stock(stock.id)
    assert len(predictions) == 1


async def test_list_by_status(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    await _create_prediction(db_session, predictor.id, stock.id, status="pending_review")
    await _create_prediction(db_session, predictor.id, stock.id, status="approved")

    repo = PredictionRepository(db_session)
    pending = await repo.list_by_status("pending_review")
    assert len(pending) == 1
    approved = await repo.list_by_status("approved")
    assert len(approved) == 1


async def test_list_recent_only_approved(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    await _create_prediction(db_session, predictor.id, stock.id, status="pending_review")
    await _create_prediction(db_session, predictor.id, stock.id, status="approved")

    repo = PredictionRepository(db_session)
    recent = await repo.list_recent()
    assert len(recent) == 1
    assert recent[0].status == "approved"


async def test_approve_prediction(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    reviewer = await create_test_user(db_session, role="admin")
    prediction = await _create_prediction(db_session, predictor.id, stock.id)

    repo = PredictionRepository(db_session)
    updated = await repo.approve(prediction, reviewer.id)
    assert updated.status == "approved"
    assert updated.reviewed_by == reviewer.id
    assert updated.reviewed_at is not None


async def test_reject_prediction(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    reviewer = await create_test_user(db_session, role="admin")
    prediction = await _create_prediction(db_session, predictor.id, stock.id)

    repo = PredictionRepository(db_session)
    updated = await repo.reject(prediction, reviewer.id)
    assert updated.status == "rejected"
    assert updated.reviewed_by == reviewer.id


async def test_list_by_predictor_pagination(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    base_time = datetime(2025, 1, 1)
    for i in range(5):
        await _create_prediction(
            db_session,
            predictor.id,
            stock.id,
            created_at=base_time - timedelta(hours=i),
        )

    repo = PredictionRepository(db_session)
    first = await repo.list_by_predictor(predictor.id, limit=3)
    assert len(first) == 3

    cursor = first[-1].created_at
    second = await repo.list_by_predictor(predictor.id, cursor=cursor, limit=3)
    assert len(second) == 2


async def test_list_by_user(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    user = await create_test_user(db_session)

    p = Prediction(
        predictor_id=predictor.id,
        stock_id=stock.id,
        target_price=Decimal("1500.00"),
        price_at_prediction=Decimal("1200.00"),
        prediction_date=date(2025, 1, 15),
        default_eval_date=date(2026, 1, 15),
        source_url="https://example.com/article",
        source_type="news_article",
        submitted_by=user.id,
        status="pending_review",
    )
    db_session.add(p)
    await db_session.flush()

    repo = PredictionRepository(db_session)
    results = await repo.list_by_user(user.id)
    assert len(results) == 1
    assert results[0].submitted_by == user.id


async def test_find_duplicate_exact_match(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    await _create_prediction(db_session, predictor.id, stock.id, status="approved")

    repo = PredictionRepository(db_session)
    dup = await repo.find_duplicate(
        predictor.id,
        stock.id,
        Decimal("1500.00"),
        date(2025, 1, 15),
    )
    assert dup is not None


async def test_find_duplicate_within_tolerance(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    await _create_prediction(db_session, predictor.id, stock.id)

    repo = PredictionRepository(db_session)
    # Target ±5% of 1500 = 1425-1575
    dup = await repo.find_duplicate(
        predictor.id,
        stock.id,
        Decimal("1520.00"),
        date(2025, 1, 20),
    )
    assert dup is not None


async def test_find_duplicate_no_match_outside_tolerance(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    await _create_prediction(db_session, predictor.id, stock.id)

    repo = PredictionRepository(db_session)
    # Target very different price
    dup = await repo.find_duplicate(
        predictor.id,
        stock.id,
        Decimal("2000.00"),
        date(2025, 1, 15),
    )
    assert dup is None


async def test_find_duplicate_no_match_outside_date_range(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    await _create_prediction(db_session, predictor.id, stock.id)

    repo = PredictionRepository(db_session)
    # Date >30 days away
    dup = await repo.find_duplicate(
        predictor.id,
        stock.id,
        Decimal("1500.00"),
        date(2025, 6, 1),
    )
    assert dup is None


async def test_find_duplicate_ignores_rejected(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    await _create_prediction(db_session, predictor.id, stock.id, status="rejected")

    repo = PredictionRepository(db_session)
    dup = await repo.find_duplicate(
        predictor.id,
        stock.id,
        Decimal("1500.00"),
        date(2025, 1, 15),
    )
    assert dup is None
