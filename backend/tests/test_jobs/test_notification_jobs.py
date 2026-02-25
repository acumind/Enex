"""Tests for notification dispatch Celery tasks."""

from unittest.mock import AsyncMock, patch

_P_SESSION_FACTORY = "app.core.database.async_session_factory"


def _make_session_ctx(mock_session):  # type: ignore[no-untyped-def]
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
    mock_ctx.__aexit__ = AsyncMock(return_value=False)
    return mock_ctx


async def test_dispatch_outcome_returns_zero_on_empty() -> None:
    from app.jobs.notifications import _dispatch_outcome_notifications

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=AsyncMock(first=lambda: None))

    with patch(_P_SESSION_FACTORY, return_value=_make_session_ctx(mock_session)):
        count = await _dispatch_outcome_notifications(["00000000-0000-0000-0000-000000000000"])
    assert count == 0


async def test_dispatch_new_prediction_returns_zero_on_missing() -> None:
    from app.jobs.notifications import _dispatch_new_prediction_notifications

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=AsyncMock(first=lambda: None))

    with patch(_P_SESSION_FACTORY, return_value=_make_session_ctx(mock_session)):
        count = await _dispatch_new_prediction_notifications("00000000-0000-0000-0000-000000000000")
    assert count == 0


def test_sync_task_catches_exception() -> None:
    with patch("app.jobs.notifications.asyncio.run", side_effect=RuntimeError("boom")):
        from app.jobs.notifications import dispatch_outcome_notifications_task

        result = dispatch_outcome_notifications_task(["some-id"])
    assert result["notifications_created"] == 0


def test_sync_new_prediction_task_catches_exception() -> None:
    with patch("app.jobs.notifications.asyncio.run", side_effect=RuntimeError("boom")):
        from app.jobs.notifications import dispatch_new_prediction_notifications_task

        result = dispatch_new_prediction_notifications_task("some-id")
    assert result["notifications_created"] == 0
