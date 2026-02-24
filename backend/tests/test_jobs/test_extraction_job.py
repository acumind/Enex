"""Tests for extraction background job — _slugify, _run_extraction, task retry."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.jobs.extraction import _slugify

# ---------------------------------------------------------------------------
# _slugify tests
# ---------------------------------------------------------------------------


def test_slugify_basic_name() -> None:
    assert _slugify("Rajat Sharma") == "rajat-sharma"


def test_slugify_special_characters() -> None:
    assert _slugify("Motilal Oswal (Research)") == "motilal-oswal-research"


def test_slugify_extra_whitespace() -> None:
    assert _slugify("  Dr. Ravi  Kumar  ") == "dr-ravi-kumar"


def test_slugify_all_special_chars() -> None:
    assert _slugify("---!!!---") == ""


def test_slugify_numbers_preserved() -> None:
    assert _slugify("Analyst123 Group") == "analyst123-group"


def test_slugify_unicode_stripped() -> None:
    # Non-ASCII chars replaced with hyphens, then stripped
    assert _slugify("café résumé") == "caf-r-sum"


def test_slugify_single_word() -> None:
    assert _slugify("CNBC") == "cnbc"


def test_slugify_already_slug() -> None:
    assert _slugify("already-a-slug") == "already-a-slug"


# ---------------------------------------------------------------------------
# _run_extraction tests (mock DB + services)
# Lazy imports inside _run_extraction must be patched at the SOURCE module.
# ---------------------------------------------------------------------------

# Common patch targets for lazy imports in _run_extraction
_P_EXTRACTION_SVC = "app.services.extraction.ExtractionService"
_P_SESSION_FACTORY = "app.core.database.async_session_factory"
_P_PREDICTOR_REPO = "app.repositories.predictor.PredictorRepository"
_P_STOCK_REPO = "app.repositories.stock.StockRepository"
_P_PRED_REPO = "app.repositories.prediction.PredictionRepository"
_P_SUGGESTION_REPO = "app.repositories.suggestion.SuggestionRepository"


@pytest.fixture
def mock_extraction_result():  # type: ignore[no-untyped-def]
    from app.schemas.extraction import ExtractionResponse, ExtractionResult

    return ExtractionResponse(
        url="https://example.com/article",
        predictions=[
            ExtractionResult(
                predictor_name="Test Analyst",
                stock_name="Test Corp",
                stock_symbol="TESTCORP",
                target_price=1500.0,
                current_price_mentioned=1200.0,
                direction="buy",
                confidence=0.9,
                source_type="news_article",
                raw_quote="Target of 1500",
            ),
        ],
        source_text_length=5000,
    )


@pytest.fixture
def mock_extraction_result_unknown_stock():  # type: ignore[no-untyped-def]
    from app.schemas.extraction import ExtractionResponse, ExtractionResult

    return ExtractionResponse(
        url="https://example.com/article",
        predictions=[
            ExtractionResult(
                predictor_name="Test Analyst",
                stock_name="Unknown Corp",
                stock_symbol="UNKNOWN",
                target_price=500.0,
                direction="buy",
                confidence=0.8,
                source_type="news_article",
            ),
        ],
        source_text_length=3000,
    )


@pytest.fixture
def mock_extraction_empty():  # type: ignore[no-untyped-def]
    from app.schemas.extraction import ExtractionResponse

    return ExtractionResponse(
        url="https://example.com/no-predictions",
        predictions=[],
        source_text_length=2000,
    )


def _make_session_ctx(mock_session):  # type: ignore[no-untyped-def]
    """Create an async context manager mock wrapping a mock session."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return mock_ctx


async def test_run_extraction_creates_predictor_and_prediction(mock_extraction_result) -> None:  # type: ignore[no-untyped-def]
    """Full flow: fetches URL, creates new predictor, creates prediction, commits."""
    from app.jobs.extraction import _run_extraction

    reviewer_id = str(uuid.uuid4())
    mock_predictor = MagicMock(id=uuid.uuid4())
    mock_stock = MagicMock(id=uuid.uuid4())
    mock_prediction = MagicMock(id=uuid.uuid4())

    mock_predictor_repo = AsyncMock()
    mock_predictor_repo.get_by_slug.return_value = None  # predictor doesn't exist
    mock_predictor_repo.create.return_value = mock_predictor

    mock_stock_repo = AsyncMock()
    mock_stock_repo.get_by_symbol.return_value = mock_stock

    mock_pred_repo = AsyncMock()
    mock_pred_repo.create.return_value = mock_prediction

    mock_session = AsyncMock()

    with (
        patch(_P_EXTRACTION_SVC) as mock_ext_svc_cls,
        patch(_P_SESSION_FACTORY, return_value=_make_session_ctx(mock_session)),
        patch(_P_PREDICTOR_REPO, return_value=mock_predictor_repo),
        patch(_P_STOCK_REPO, return_value=mock_stock_repo),
        patch(_P_PRED_REPO, return_value=mock_pred_repo),
    ):
        mock_ext_svc_cls.return_value.extract_from_url = AsyncMock(return_value=mock_extraction_result)

        await _run_extraction(None, reviewer_id, "https://example.com/article")

    # Predictor was looked up by slug and created
    mock_predictor_repo.get_by_slug.assert_awaited_once_with("test-analyst")
    mock_predictor_repo.create.assert_awaited_once()

    # Stock was resolved
    mock_stock_repo.get_by_symbol.assert_awaited_once_with("TESTCORP")

    # Prediction was created
    mock_pred_repo.create.assert_awaited_once()
    created_pred = mock_pred_repo.create.call_args[0][0]
    assert created_pred.predictor_id == mock_predictor.id
    assert created_pred.stock_id == mock_stock.id
    assert created_pred.extraction_method == "ai_auto"
    assert created_pred.status == "pending_review"

    # Session committed
    mock_session.commit.assert_awaited_once()


async def test_run_extraction_reuses_existing_predictor(mock_extraction_result) -> None:  # type: ignore[no-untyped-def]
    """If predictor already exists by slug, reuse it instead of creating."""
    from app.jobs.extraction import _run_extraction

    reviewer_id = str(uuid.uuid4())
    existing_predictor = MagicMock(id=uuid.uuid4())
    mock_stock = MagicMock(id=uuid.uuid4())
    mock_prediction = MagicMock(id=uuid.uuid4())

    mock_predictor_repo = AsyncMock()
    mock_predictor_repo.get_by_slug.return_value = existing_predictor  # already exists

    mock_stock_repo = AsyncMock()
    mock_stock_repo.get_by_symbol.return_value = mock_stock

    mock_pred_repo = AsyncMock()
    mock_pred_repo.create.return_value = mock_prediction

    mock_session = AsyncMock()

    with (
        patch(_P_EXTRACTION_SVC) as mock_ext_svc_cls,
        patch(_P_SESSION_FACTORY, return_value=_make_session_ctx(mock_session)),
        patch(_P_PREDICTOR_REPO, return_value=mock_predictor_repo),
        patch(_P_STOCK_REPO, return_value=mock_stock_repo),
        patch(_P_PRED_REPO, return_value=mock_pred_repo),
    ):
        mock_ext_svc_cls.return_value.extract_from_url = AsyncMock(return_value=mock_extraction_result)

        await _run_extraction(None, reviewer_id, "https://example.com/article")

    # Predictor was NOT created (reused existing)
    mock_predictor_repo.create.assert_not_awaited()

    # Prediction still created with existing predictor
    created_pred = mock_pred_repo.create.call_args[0][0]
    assert created_pred.predictor_id == existing_predictor.id


async def test_run_extraction_skips_unknown_stock(mock_extraction_result_unknown_stock) -> None:  # type: ignore[no-untyped-def]
    """If stock symbol not found in DB, skip that prediction."""
    from app.jobs.extraction import _run_extraction

    reviewer_id = str(uuid.uuid4())

    mock_predictor_repo = AsyncMock()
    mock_predictor_repo.get_by_slug.return_value = MagicMock(id=uuid.uuid4())

    mock_stock_repo = AsyncMock()
    mock_stock_repo.get_by_symbol.return_value = None  # stock not found

    mock_pred_repo = AsyncMock()

    mock_session = AsyncMock()

    with (
        patch(_P_EXTRACTION_SVC) as mock_ext_svc_cls,
        patch(_P_SESSION_FACTORY, return_value=_make_session_ctx(mock_session)),
        patch(_P_PREDICTOR_REPO, return_value=mock_predictor_repo),
        patch(_P_STOCK_REPO, return_value=mock_stock_repo),
        patch(_P_PRED_REPO, return_value=mock_pred_repo),
    ):
        mock_ext_svc_cls.return_value.extract_from_url = AsyncMock(
            return_value=mock_extraction_result_unknown_stock,
        )

        await _run_extraction(None, reviewer_id, "https://example.com/article")

    # Prediction was NOT created (stock not found)
    mock_pred_repo.create.assert_not_awaited()


async def test_run_extraction_no_predictions(mock_extraction_empty) -> None:  # type: ignore[no-untyped-def]
    """If AI extraction returns no predictions, just commit (no-op)."""
    from app.jobs.extraction import _run_extraction

    reviewer_id = str(uuid.uuid4())

    mock_session = AsyncMock()

    with (
        patch(_P_EXTRACTION_SVC) as mock_ext_svc_cls,
        patch(_P_SESSION_FACTORY, return_value=_make_session_ctx(mock_session)),
        patch(_P_PRED_REPO) as mock_pred_repo_cls,
        patch(_P_PREDICTOR_REPO),
        patch(_P_STOCK_REPO),
    ):
        mock_ext_svc_cls.return_value.extract_from_url = AsyncMock(return_value=mock_extraction_empty)

        await _run_extraction(None, reviewer_id, "https://example.com/no-predictions")

    # No predictions created
    mock_pred_repo_cls.return_value.create.assert_not_called()
    # Session still committed
    mock_session.commit.assert_awaited_once()


async def test_run_extraction_links_suggestion(mock_extraction_result) -> None:  # type: ignore[no-untyped-def]
    """When suggestion_id is provided, update suggestion.promoted_to after extraction."""
    from app.jobs.extraction import _run_extraction

    suggestion_id = str(uuid.uuid4())
    reviewer_id = str(uuid.uuid4())
    mock_prediction = MagicMock(id=uuid.uuid4())
    mock_suggestion = MagicMock()

    mock_predictor_repo = AsyncMock()
    mock_predictor_repo.get_by_slug.return_value = MagicMock(id=uuid.uuid4())

    mock_stock_repo = AsyncMock()
    mock_stock_repo.get_by_symbol.return_value = MagicMock(id=uuid.uuid4())

    mock_pred_repo = AsyncMock()
    mock_pred_repo.create.return_value = mock_prediction

    mock_suggestion_repo = AsyncMock()
    mock_suggestion_repo.get_by_id.return_value = mock_suggestion

    mock_session = AsyncMock()

    with (
        patch(_P_EXTRACTION_SVC) as mock_ext_svc_cls,
        patch(_P_SESSION_FACTORY, return_value=_make_session_ctx(mock_session)),
        patch(_P_PREDICTOR_REPO, return_value=mock_predictor_repo),
        patch(_P_STOCK_REPO, return_value=mock_stock_repo),
        patch(_P_PRED_REPO, return_value=mock_pred_repo),
        patch(_P_SUGGESTION_REPO, return_value=mock_suggestion_repo),
    ):
        mock_ext_svc_cls.return_value.extract_from_url = AsyncMock(return_value=mock_extraction_result)

        await _run_extraction(suggestion_id, reviewer_id, "https://example.com/article")

    # Suggestion was looked up and linked
    mock_suggestion_repo.get_by_id.assert_awaited_once()
    assert mock_suggestion.promoted_to == mock_prediction.id
    mock_session.flush.assert_awaited()


async def test_run_extraction_no_suggestion_link_when_id_is_none(mock_extraction_result) -> None:  # type: ignore[no-untyped-def]
    """When suggestion_id is None, skip suggestion linking."""
    from app.jobs.extraction import _run_extraction

    reviewer_id = str(uuid.uuid4())

    mock_predictor_repo = AsyncMock()
    mock_predictor_repo.get_by_slug.return_value = MagicMock(id=uuid.uuid4())

    mock_stock_repo = AsyncMock()
    mock_stock_repo.get_by_symbol.return_value = MagicMock(id=uuid.uuid4())

    mock_pred_repo = AsyncMock()
    mock_pred_repo.create.return_value = MagicMock(id=uuid.uuid4())

    mock_session = AsyncMock()

    with (
        patch(_P_EXTRACTION_SVC) as mock_ext_svc_cls,
        patch(_P_SESSION_FACTORY, return_value=_make_session_ctx(mock_session)),
        patch(_P_PREDICTOR_REPO, return_value=mock_predictor_repo),
        patch(_P_STOCK_REPO, return_value=mock_stock_repo),
        patch(_P_PRED_REPO, return_value=mock_pred_repo),
        patch(_P_SUGGESTION_REPO) as mock_sugg_repo_cls,
    ):
        mock_ext_svc_cls.return_value.extract_from_url = AsyncMock(return_value=mock_extraction_result)

        await _run_extraction(None, reviewer_id, "https://example.com/article")

    # SuggestionRepository never instantiated
    mock_sugg_repo_cls.return_value.get_by_id.assert_not_called()


# ---------------------------------------------------------------------------
# Celery task tests
# ---------------------------------------------------------------------------


def test_extract_prediction_task_success() -> None:
    """Task returns success dict on happy path."""
    with patch("app.jobs.extraction.asyncio.run") as mock_run:
        from app.jobs.extraction import extract_prediction_task

        result = extract_prediction_task(None, str(uuid.uuid4()), "https://example.com")

    assert result == {"status": "ok", "url": "https://example.com"}
    mock_run.assert_called_once()


def test_extract_prediction_task_retries_on_failure() -> None:
    """Task calls self.retry on exception."""
    with patch("app.jobs.extraction.asyncio.run", side_effect=RuntimeError("boom")):
        from app.jobs.extraction import extract_prediction_task

        # RuntimeError propagates when self.retry is not fully mocked
        with pytest.raises(RuntimeError, match="boom"):
            extract_prediction_task(None, str(uuid.uuid4()), "https://example.com")
