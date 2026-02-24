"""Tests for scorecard update background job."""

from unittest.mock import AsyncMock, patch

import pytest

_P_SESSION_FACTORY = "app.core.database.async_session_factory"
_P_EVAL_SVC = "app.services.evaluation.EvaluationService"


def _make_session_ctx(mock_session):  # type: ignore[no-untyped-def]
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return mock_ctx


async def test_run_scorecard_update_calls_service() -> None:
    from app.jobs.scorecard import _run_scorecard_update

    mock_session = AsyncMock()
    mock_service = AsyncMock()
    mock_service.update_all_scorecards.return_value = 10

    with (
        patch(_P_SESSION_FACTORY, return_value=_make_session_ctx(mock_session)),
        patch(_P_EVAL_SVC, return_value=mock_service),
    ):
        result = await _run_scorecard_update()

    assert result == {"scorecards_updated": 10}
    mock_service.update_all_scorecards.assert_awaited_once()
    mock_session.commit.assert_awaited_once()


def test_update_scorecards_task_success() -> None:
    with patch("app.jobs.scorecard.asyncio.run", return_value={"scorecards_updated": 5}):
        from app.jobs.scorecard import update_scorecards_task

        result = update_scorecards_task()
    assert result["scorecards_updated"] == 5


def test_update_scorecards_task_retries_on_failure() -> None:
    with patch("app.jobs.scorecard.asyncio.run", side_effect=RuntimeError("boom")):
        from app.jobs.scorecard import update_scorecards_task

        with pytest.raises(RuntimeError, match="boom"):
            update_scorecards_task()
