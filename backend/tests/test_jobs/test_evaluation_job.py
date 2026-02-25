"""Tests for evaluation background job."""

from unittest.mock import AsyncMock, patch

import pytest

_P_SESSION_FACTORY = "app.core.database.async_session_factory"
_P_EVAL_SVC = "app.services.evaluation.EvaluationService"


def _make_session_ctx(mock_session):  # type: ignore[no-untyped-def]
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return mock_ctx


async def test_run_evaluation_calls_service() -> None:
    from app.jobs.evaluation import _run_evaluation

    mock_session = AsyncMock()
    mock_service = AsyncMock()
    mock_service.evaluate_pending_predictions.return_value = (5, [])

    with (
        patch(_P_SESSION_FACTORY, return_value=_make_session_ctx(mock_session)),
        patch(_P_EVAL_SVC, return_value=mock_service),
    ):
        result = await _run_evaluation()

    assert result == {"predictions_evaluated": 5}
    mock_service.evaluate_pending_predictions.assert_awaited_once()
    mock_session.commit.assert_awaited_once()


def test_evaluate_predictions_task_success() -> None:
    with patch("app.jobs.evaluation.asyncio.run", return_value={"predictions_evaluated": 3}):
        from app.jobs.evaluation import evaluate_predictions_task

        result = evaluate_predictions_task()
    assert result["predictions_evaluated"] == 3


def test_evaluate_predictions_task_retries_on_failure() -> None:
    with patch("app.jobs.evaluation.asyncio.run", side_effect=RuntimeError("boom")):
        from app.jobs.evaluation import evaluate_predictions_task

        with pytest.raises(RuntimeError, match="boom"):
            evaluate_predictions_task()
