"""Tests for SuggestionRepository CRUD and queries."""

import uuid
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import PredictionSuggestion
from app.repositories.suggestion import SuggestionRepository
from tests.conftest import create_test_predictor, create_test_stock, create_test_user


async def _create_suggestion(
    db_session: AsyncSession,
    user_id: uuid.UUID,
    *,
    status: str = "pending",
    created_at: datetime | None = None,
) -> PredictionSuggestion:
    suggestion = PredictionSuggestion(
        url="https://example.com/article",
        note="Check this prediction",
        submitted_by=user_id,
        status=status,
    )
    if created_at is not None:
        suggestion.created_at = created_at  # type: ignore[assignment]
    db_session.add(suggestion)
    await db_session.flush()
    return suggestion


async def test_create_suggestion(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    repo = SuggestionRepository(db_session)

    suggestion = PredictionSuggestion(
        url="https://example.com/article",
        note="A prediction",
        submitted_by=user.id,
        status="pending",
    )
    result = await repo.create(suggestion)
    assert result.id is not None
    assert result.url == "https://example.com/article"
    assert result.status == "pending"


async def test_list_by_status(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    await _create_suggestion(db_session, user.id, status="pending")
    await _create_suggestion(db_session, user.id, status="pending")
    await _create_suggestion(db_session, user.id, status="dismissed")

    repo = SuggestionRepository(db_session)
    pending = await repo.list_by_status("pending")
    assert len(pending) == 2
    dismissed = await repo.list_by_status("dismissed")
    assert len(dismissed) == 1


async def test_list_by_user(db_session: AsyncSession) -> None:
    user1 = await create_test_user(db_session)
    user2 = await create_test_user(db_session)
    await _create_suggestion(db_session, user1.id)
    await _create_suggestion(db_session, user1.id)
    await _create_suggestion(db_session, user2.id)

    repo = SuggestionRepository(db_session)
    user1_suggestions = await repo.list_by_user(user1.id)
    assert len(user1_suggestions) == 2
    user2_suggestions = await repo.list_by_user(user2.id)
    assert len(user2_suggestions) == 1


async def test_promote(db_session: AsyncSession) -> None:
    from datetime import date
    from decimal import Decimal

    from app.models.prediction import Prediction

    user = await create_test_user(db_session)
    reviewer = await create_test_user(db_session, role="admin")
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)

    # Create a real prediction to satisfy FK constraint
    prediction = Prediction(
        predictor_id=predictor.id,
        stock_id=stock.id,
        target_price=Decimal("1500.00"),
        price_at_prediction=Decimal("1200.00"),
        prediction_date=date(2025, 1, 15),
        default_eval_date=date(2026, 1, 15),
        source_url="https://example.com/article",
        source_type="news_article",
        status="pending_review",
    )
    db_session.add(prediction)
    await db_session.flush()

    suggestion = await _create_suggestion(db_session, user.id)

    repo = SuggestionRepository(db_session)
    promoted = await repo.promote(suggestion, prediction.id, reviewer.id)
    assert promoted.status == "promoted"
    assert promoted.promoted_to == prediction.id
    assert promoted.reviewed_by == reviewer.id
    assert promoted.reviewed_at is not None


async def test_dismiss(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    reviewer = await create_test_user(db_session, role="admin")
    suggestion = await _create_suggestion(db_session, user.id)

    repo = SuggestionRepository(db_session)
    dismissed = await repo.dismiss(suggestion, reviewer.id)
    assert dismissed.status == "dismissed"
    assert dismissed.reviewed_by == reviewer.id
    assert dismissed.reviewed_at is not None


async def test_list_by_status_pagination(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    base_time = datetime(2025, 1, 1)
    for i in range(5):
        await _create_suggestion(
            db_session,
            user.id,
            created_at=base_time - timedelta(hours=i),
        )

    repo = SuggestionRepository(db_session)
    first = await repo.list_by_status("pending", limit=3)
    assert len(first) == 3

    cursor = first[-1].created_at
    second = await repo.list_by_status("pending", cursor=cursor, limit=3)
    assert len(second) == 2
