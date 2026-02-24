"""Tests for PredictionService — creation, duplicate detection, extraction metadata, date math."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.schemas.common import ExtractionMethod
from app.schemas.prediction import PredictionCreate
from app.services.prediction import PredictionService, _add_months, _compute_default_eval_date
from tests.conftest import create_test_predictor, create_test_stock, create_test_user

# ---------------------------------------------------------------------------
# _add_months date arithmetic tests
# ---------------------------------------------------------------------------


def test_add_months_basic() -> None:
    assert _add_months(date(2025, 1, 15), 12) == date(2026, 1, 15)


def test_add_months_mid_year() -> None:
    assert _add_months(date(2025, 6, 10), 3) == date(2025, 9, 10)


def test_add_months_year_boundary() -> None:
    assert _add_months(date(2025, 11, 1), 3) == date(2026, 2, 1)


def test_add_months_clamp_day_to_month_end() -> None:
    # Jan 31 + 1 month → Feb 28 (non-leap year)
    assert _add_months(date(2025, 1, 31), 1) == date(2025, 2, 28)


def test_add_months_leap_year_feb() -> None:
    # Jan 31 + 1 month in a leap year → Feb 29
    assert _add_months(date(2024, 1, 31), 1) == date(2024, 2, 29)


def test_add_months_clamp_day_march_to_feb() -> None:
    # March 31 + 11 months → Feb 28 of next year
    assert _add_months(date(2025, 3, 31), 11) == date(2026, 2, 28)


def test_add_months_zero() -> None:
    assert _add_months(date(2025, 6, 15), 0) == date(2025, 6, 15)


def test_add_months_large() -> None:
    # 24 months = 2 years
    assert _add_months(date(2025, 1, 15), 24) == date(2027, 1, 15)


def test_add_months_dec_to_dec() -> None:
    assert _add_months(date(2025, 12, 15), 12) == date(2026, 12, 15)


def test_add_months_end_of_year() -> None:
    # Dec 31 + 2 months → Feb 28
    assert _add_months(date(2025, 12, 31), 2) == date(2026, 2, 28)


# ---------------------------------------------------------------------------
# _compute_default_eval_date tests
# ---------------------------------------------------------------------------


def test_compute_default_eval_date_with_target() -> None:
    target = date(2025, 6, 30)
    assert _compute_default_eval_date(date(2025, 1, 15), target) == target


def test_compute_default_eval_date_without_target() -> None:
    # Should be prediction_date + 12 months
    assert _compute_default_eval_date(date(2025, 1, 15), None) == date(2026, 1, 15)


def test_compute_default_eval_date_end_of_month() -> None:
    assert _compute_default_eval_date(date(2025, 1, 31), None) == date(2026, 1, 31)


def _prediction_data(predictor_id, stock_id, **overrides):  # type: ignore[no-untyped-def]
    defaults = {
        "predictor_id": predictor_id,
        "stock_id": stock_id,
        "target_price": Decimal("1500.00"),
        "price_at_prediction": Decimal("1200.00"),
        "prediction_date": date(2025, 1, 15),
        "source_url": "https://example.com/article",
        "source_type": "news_article",
    }
    defaults.update(overrides)
    return PredictionCreate(**defaults)


async def test_create_prediction(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    user = await create_test_user(db_session)
    service = PredictionService(db_session)

    data = _prediction_data(predictor.id, stock.id)
    with patch("app.jobs.archive.archive_url_task"):
        result = await service.create(data, submitted_by=user.id)

    assert result.predictor_id == predictor.id
    assert result.stock_id == stock.id
    assert result.status == "pending_review"
    assert result.submitted_by == user.id


async def test_create_with_extraction_metadata(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    service = PredictionService(db_session)

    data = _prediction_data(
        predictor.id,
        stock.id,
        extraction_method=ExtractionMethod.ai_assisted,
        ai_confidence=Decimal("0.85"),
    )
    with patch("app.jobs.archive.archive_url_task"):
        result = await service.create(data)

    assert result.extraction_method == "ai_assisted"
    assert result.ai_confidence == Decimal("0.85")


async def test_create_with_nonexistent_predictor(db_session: AsyncSession) -> None:
    import uuid

    stock = await create_test_stock(db_session)
    service = PredictionService(db_session)

    data = _prediction_data(uuid.uuid4(), stock.id)
    with pytest.raises(NotFoundError, match="Predictor not found"):
        await service.create(data)


async def test_create_with_nonexistent_stock(db_session: AsyncSession) -> None:
    import uuid

    predictor = await create_test_predictor(db_session)
    service = PredictionService(db_session)

    data = _prediction_data(predictor.id, uuid.uuid4())
    with pytest.raises(NotFoundError, match="Stock not found"):
        await service.create(data)


async def test_duplicate_detection_raises_conflict(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    service = PredictionService(db_session)

    data = _prediction_data(predictor.id, stock.id)
    with patch("app.jobs.archive.archive_url_task"):
        await service.create(data)

    # Same prediction again → conflict
    data2 = _prediction_data(predictor.id, stock.id)
    with pytest.raises(ConflictError):
        await service.create(data2)


async def test_list_by_user(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session)
    stock = await create_test_stock(db_session)
    user = await create_test_user(db_session)
    service = PredictionService(db_session)

    data = _prediction_data(predictor.id, stock.id)
    with patch("app.jobs.archive.archive_url_task"):
        await service.create(data, submitted_by=user.id)

    result = await service.list_by_user(user.id)
    assert len(result.items) == 1
    assert result.items[0].submitted_by == user.id
