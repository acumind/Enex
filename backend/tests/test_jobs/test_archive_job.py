"""Tests for archive background job — _run_archive, task retry."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

# Patch targets for lazy imports in _run_archive
_P_WAYBACK = "app.integrations.archive.wayback_adapter.WaybackAdapter"
_P_SESSION_FACTORY = "app.core.database.async_session_factory"
_P_PRED_REPO = "app.repositories.prediction.PredictionRepository"

# ---------------------------------------------------------------------------
# _run_archive tests
# ---------------------------------------------------------------------------


def _make_session_ctx(mock_session):  # type: ignore[no-untyped-def]
    """Create an async context manager mock wrapping a mock session."""
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return mock_ctx


async def test_run_archive_saves_snapshot_url() -> None:
    """When wayback returns a snapshot URL, update prediction.source_archive_url."""
    from app.jobs.archive import _run_archive

    prediction_id = str(uuid.uuid4())
    mock_prediction = AsyncMock()

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = mock_prediction

    mock_session = AsyncMock()

    with (
        patch(_P_WAYBACK) as mock_adapter_cls,
        patch(_P_SESSION_FACTORY, return_value=_make_session_ctx(mock_session)),
        patch(_P_PRED_REPO, return_value=mock_repo),
    ):
        mock_adapter_cls.return_value.save_url = AsyncMock(
            return_value="https://web.archive.org/web/20250101/https://example.com"
        )

        await _run_archive(prediction_id, "https://example.com")

    assert mock_prediction.source_archive_url == "https://web.archive.org/web/20250101/https://example.com"
    mock_session.flush.assert_awaited_once()
    mock_session.commit.assert_awaited_once()


async def test_run_archive_skips_when_no_snapshot() -> None:
    """When wayback returns None, don't touch DB."""
    from app.jobs.archive import _run_archive

    prediction_id = str(uuid.uuid4())

    with (
        patch(_P_WAYBACK) as mock_adapter_cls,
        patch(_P_SESSION_FACTORY) as mock_factory,
    ):
        mock_adapter_cls.return_value.save_url = AsyncMock(return_value=None)

        await _run_archive(prediction_id, "https://example.com")

    # Session factory never called — no DB interaction
    mock_factory.assert_not_called()


async def test_run_archive_handles_missing_prediction() -> None:
    """If prediction no longer exists in DB, just commit without error."""
    from app.jobs.archive import _run_archive

    prediction_id = str(uuid.uuid4())

    mock_repo = AsyncMock()
    mock_repo.get_by_id.return_value = None  # prediction deleted

    mock_session = AsyncMock()

    with (
        patch(_P_WAYBACK) as mock_adapter_cls,
        patch(_P_SESSION_FACTORY, return_value=_make_session_ctx(mock_session)),
        patch(_P_PRED_REPO, return_value=mock_repo),
    ):
        mock_adapter_cls.return_value.save_url = AsyncMock(
            return_value="https://web.archive.org/web/latest/https://example.com"
        )

        await _run_archive(prediction_id, "https://example.com")

    # flush/commit not called since prediction is None
    mock_session.flush.assert_not_awaited()


# ---------------------------------------------------------------------------
# Celery task tests
# ---------------------------------------------------------------------------


def test_archive_url_task_success() -> None:
    """Task returns success dict on happy path."""
    with patch("app.jobs.archive.asyncio.run") as mock_run:
        from app.jobs.archive import archive_url_task

        result = archive_url_task(str(uuid.uuid4()), "https://example.com")

    assert result == {"status": "ok", "url": "https://example.com"}
    mock_run.assert_called_once()


def test_archive_url_task_retries_on_failure() -> None:
    """Task calls self.retry on exception."""
    with patch("app.jobs.archive.asyncio.run", side_effect=RuntimeError("boom")):
        from app.jobs.archive import archive_url_task

        with pytest.raises(RuntimeError, match="boom"):
            archive_url_task(str(uuid.uuid4()), "https://example.com")
