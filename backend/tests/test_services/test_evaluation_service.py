"""Tests for EvaluationService — core evaluation logic."""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.evaluation import EvaluationService

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_prediction(
    *,
    target_price: Decimal = Decimal("1500.00"),
    price_at_prediction: Decimal = Decimal("1200.00"),
    prediction_date: date = date(2025, 1, 15),
    stock_id: str = "stock-1",
    prediction_id: str = "pred-1",
) -> MagicMock:
    pred = MagicMock()
    pred.id = prediction_id
    pred.stock_id = stock_id
    pred.target_price = target_price
    pred.price_at_prediction = price_at_prediction
    pred.prediction_date = prediction_date
    return pred


def _make_price_row(close_price: Decimal, adjusted_close: Decimal | None = None) -> MagicMock:
    row = MagicMock()
    row.close_price = close_price
    row.adjusted_close = adjusted_close
    return row


# ---------------------------------------------------------------------------
# _evaluate_bullish / _evaluate_bearish (via _evaluate_single)
# ---------------------------------------------------------------------------


@pytest.fixture
def service() -> EvaluationService:
    """Create service with mocked session (tolerance = 5%)."""
    mock_session = AsyncMock()
    with patch("app.services.evaluation.get_settings") as mock_settings:
        mock_settings.return_value.OUTCOME_TOLERANCE_PCT = 5.0
        svc = EvaluationService(mock_session)
    return svc


async def test_bullish_hit(service: EvaluationService) -> None:
    """Bullish: highest >= target → hit."""
    prediction = _make_prediction(target_price=Decimal("1500.00"), price_at_prediction=Decimal("1200.00"))
    service.price_repo = AsyncMock()
    service.price_repo.get_price_on_date.return_value = _make_price_row(Decimal("1480.00"))
    service.price_repo.get_high_low_in_range.return_value = (Decimal("1550.00"), Decimal("1100.00"))

    outcome = await service._evaluate_single(prediction, date(2026, 1, 15))
    assert outcome is not None
    assert outcome.outcome_status == "hit"
    assert outcome.highest_price == Decimal("1550.00")


async def test_bullish_partial_hit(service: EvaluationService) -> None:
    """Bullish: highest >= target*0.95 but < target → partial_hit."""
    prediction = _make_prediction(target_price=Decimal("1500.00"), price_at_prediction=Decimal("1200.00"))
    service.price_repo = AsyncMock()
    service.price_repo.get_price_on_date.return_value = _make_price_row(Decimal("1430.00"))
    # 1500 * 0.95 = 1425. Highest = 1450 → partial hit
    service.price_repo.get_high_low_in_range.return_value = (Decimal("1450.00"), Decimal("1100.00"))

    outcome = await service._evaluate_single(prediction, date(2026, 1, 15))
    assert outcome is not None
    assert outcome.outcome_status == "partial_hit"


async def test_bullish_miss(service: EvaluationService) -> None:
    """Bullish: highest < target*0.95 → miss."""
    prediction = _make_prediction(target_price=Decimal("1500.00"), price_at_prediction=Decimal("1200.00"))
    service.price_repo = AsyncMock()
    service.price_repo.get_price_on_date.return_value = _make_price_row(Decimal("1300.00"))
    # 1500 * 0.95 = 1425. Highest = 1400 → miss
    service.price_repo.get_high_low_in_range.return_value = (Decimal("1400.00"), Decimal("1100.00"))

    outcome = await service._evaluate_single(prediction, date(2026, 1, 15))
    assert outcome is not None
    assert outcome.outcome_status == "miss"


async def test_bearish_hit(service: EvaluationService) -> None:
    """Bearish: lowest <= target → hit."""
    prediction = _make_prediction(target_price=Decimal("900.00"), price_at_prediction=Decimal("1200.00"))
    service.price_repo = AsyncMock()
    service.price_repo.get_price_on_date.return_value = _make_price_row(Decimal("880.00"))
    service.price_repo.get_high_low_in_range.return_value = (Decimal("1250.00"), Decimal("870.00"))

    outcome = await service._evaluate_single(prediction, date(2026, 1, 15))
    assert outcome is not None
    assert outcome.outcome_status == "hit"
    assert outcome.lowest_price == Decimal("870.00")


async def test_bearish_partial_hit(service: EvaluationService) -> None:
    """Bearish: lowest <= target*1.05 but > target → partial_hit."""
    prediction = _make_prediction(target_price=Decimal("900.00"), price_at_prediction=Decimal("1200.00"))
    service.price_repo = AsyncMock()
    service.price_repo.get_price_on_date.return_value = _make_price_row(Decimal("920.00"))
    # 900 * 1.05 = 945. Lowest = 940 → partial hit
    service.price_repo.get_high_low_in_range.return_value = (Decimal("1250.00"), Decimal("940.00"))

    outcome = await service._evaluate_single(prediction, date(2026, 1, 15))
    assert outcome is not None
    assert outcome.outcome_status == "partial_hit"


async def test_bearish_miss(service: EvaluationService) -> None:
    """Bearish: lowest > target*1.05 → miss."""
    prediction = _make_prediction(target_price=Decimal("900.00"), price_at_prediction=Decimal("1200.00"))
    service.price_repo = AsyncMock()
    service.price_repo.get_price_on_date.return_value = _make_price_row(Decimal("1000.00"))
    # 900 * 1.05 = 945. Lowest = 960 → miss
    service.price_repo.get_high_low_in_range.return_value = (Decimal("1250.00"), Decimal("960.00"))

    outcome = await service._evaluate_single(prediction, date(2026, 1, 15))
    assert outcome is not None
    assert outcome.outcome_status == "miss"


async def test_no_price_data_returns_none(service: EvaluationService) -> None:
    """When no price data available, skip evaluation."""
    prediction = _make_prediction()
    service.price_repo = AsyncMock()
    service.price_repo.get_price_on_date.return_value = None

    outcome = await service._evaluate_single(prediction, date(2026, 1, 15))
    assert outcome is None


async def test_deviation_pct_calculation(service: EvaluationService) -> None:
    """Verify deviation_pct = (actual - target) / target * 100."""
    prediction = _make_prediction(target_price=Decimal("1500.00"))
    service.price_repo = AsyncMock()
    # actual = 1400, target = 1500 → deviation = (1400-1500)/1500*100 = -6.67
    service.price_repo.get_price_on_date.return_value = _make_price_row(Decimal("1400.00"))
    service.price_repo.get_high_low_in_range.return_value = (Decimal("1600.00"), Decimal("1300.00"))

    outcome = await service._evaluate_single(prediction, date(2026, 1, 15))
    assert outcome is not None
    assert outcome.deviation_pct == Decimal("-6.67")


# ---------------------------------------------------------------------------
# evaluate_pending_predictions
# ---------------------------------------------------------------------------


async def test_evaluate_pending_predictions(service: EvaluationService) -> None:
    """Mocked flow: find eligible predictions, evaluate each, create outcomes."""
    pred1 = _make_prediction(prediction_id="p1", target_price=Decimal("1500.00"))
    pred2 = _make_prediction(prediction_id="p2", target_price=Decimal("800.00"), price_at_prediction=Decimal("1000.00"))

    service.outcome_repo = AsyncMock()
    service.outcome_repo.find_ready_for_evaluation.return_value = [pred1, pred2]
    service.outcome_repo.create = AsyncMock()

    service.price_repo = AsyncMock()
    service.price_repo.get_price_on_date.return_value = _make_price_row(Decimal("1500.00"))
    service.price_repo.get_high_low_in_range.return_value = (Decimal("1600.00"), Decimal("700.00"))

    count, evaluated_ids = await service.evaluate_pending_predictions(date(2026, 1, 15))
    assert count == 2
    assert len(evaluated_ids) == 2
    assert service.outcome_repo.create.await_count == 2


# ---------------------------------------------------------------------------
# Streak computation
# ---------------------------------------------------------------------------


def test_evaluate_bullish_method_hit(service: EvaluationService) -> None:
    assert service._evaluate_bullish(Decimal("100"), Decimal("100")) == "hit"


def test_evaluate_bullish_method_partial(service: EvaluationService) -> None:
    # 100 * 0.95 = 95. highest = 96 → partial
    assert service._evaluate_bullish(Decimal("100"), Decimal("96")) == "partial_hit"


def test_evaluate_bullish_method_miss(service: EvaluationService) -> None:
    # 100 * 0.95 = 95. highest = 94 → miss
    assert service._evaluate_bullish(Decimal("100"), Decimal("94")) == "miss"


def test_evaluate_bullish_none_highest(service: EvaluationService) -> None:
    assert service._evaluate_bullish(Decimal("100"), None) == "miss"


def test_evaluate_bearish_method_hit(service: EvaluationService) -> None:
    assert service._evaluate_bearish(Decimal("100"), Decimal("100")) == "hit"


def test_evaluate_bearish_method_partial(service: EvaluationService) -> None:
    # 100 * 1.05 = 105. lowest = 103 → partial
    assert service._evaluate_bearish(Decimal("100"), Decimal("103")) == "partial_hit"


def test_evaluate_bearish_method_miss(service: EvaluationService) -> None:
    # 100 * 1.05 = 105. lowest = 106 → miss
    assert service._evaluate_bearish(Decimal("100"), Decimal("106")) == "miss"


def test_evaluate_bearish_none_lowest(service: EvaluationService) -> None:
    assert service._evaluate_bearish(Decimal("100"), None) == "miss"
