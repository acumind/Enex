"""Tests for notification dispatch Celery tasks."""

from unittest.mock import AsyncMock, MagicMock, patch

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


# --- Email dispatch tests ---


async def test_send_outcome_emails_disabled_by_default() -> None:
    """When NOTIFICATION_EMAIL_ENABLED is False, no emails are sent."""
    from app.jobs.notifications import _send_outcome_emails

    mock_session = AsyncMock()

    with patch("app.core.config.get_settings") as mock_get:
        mock_get.return_value = MagicMock(NOTIFICATION_EMAIL_ENABLED=False)
        await _send_outcome_emails(mock_session, ["uid1"], "SYM", "Stock", "pid1")

    # Session should not have been queried
    mock_session.execute.assert_not_called()


async def test_send_outcome_emails_enabled_sends_to_verified() -> None:
    """When enabled, sends email only to users with verified email."""
    from app.jobs.notifications import _send_outcome_emails

    mock_user = MagicMock()
    mock_user.id = "u1"
    mock_user.email = "a@b.com"

    mock_session = AsyncMock()
    # First call: PredictionOutcome query (outcome_status) — sync result methods
    outcome_result = MagicMock()
    outcome_result.scalar_one_or_none.return_value = "hit"
    # Second call: User query — sync result methods
    user_result = MagicMock()
    user_result.scalars.return_value = MagicMock(all=lambda: [mock_user])
    mock_session.execute = AsyncMock(side_effect=[outcome_result, user_result])

    with (
        patch("app.core.config.get_settings") as mock_get,
        patch("app.integrations.email.resend_adapter.ResendAdapter") as mock_adapter_cls,
    ):
        mock_get.return_value = MagicMock(NOTIFICATION_EMAIL_ENABLED=True)
        mock_adapter = AsyncMock()
        mock_adapter_cls.return_value = mock_adapter

        await _send_outcome_emails(mock_session, ["u1"], "SYM", "Stock", "pid1")

    mock_adapter.send_notification.assert_awaited_once()
    call_args = mock_adapter.send_notification.call_args
    assert call_args[0][0] == "a@b.com"
    assert "SYM" in call_args[0][1]


async def test_send_new_prediction_emails_disabled() -> None:
    """When NOTIFICATION_EMAIL_ENABLED is False, no emails are sent."""
    from app.jobs.notifications import _send_new_prediction_emails

    mock_session = AsyncMock()

    with patch("app.core.config.get_settings") as mock_get:
        mock_get.return_value = MagicMock(NOTIFICATION_EMAIL_ENABLED=False)
        await _send_new_prediction_emails(mock_session, ["uid1"], "Analyst", "analyst-slug", "SYM", "Stock")

    mock_session.execute.assert_not_called()


async def test_send_new_prediction_emails_enabled_sends_to_verified() -> None:
    """When enabled, sends email only to users with verified email."""
    from app.jobs.notifications import _send_new_prediction_emails

    mock_user = MagicMock()
    mock_user.id = "u1"
    mock_user.email = "x@y.com"

    mock_session = AsyncMock()
    user_result = MagicMock()
    user_result.scalars.return_value = MagicMock(all=lambda: [mock_user])
    mock_session.execute = AsyncMock(return_value=user_result)

    with (
        patch("app.core.config.get_settings") as mock_get,
        patch("app.integrations.email.resend_adapter.ResendAdapter") as mock_adapter_cls,
    ):
        mock_get.return_value = MagicMock(NOTIFICATION_EMAIL_ENABLED=True)
        mock_adapter = AsyncMock()
        mock_adapter_cls.return_value = mock_adapter

        await _send_new_prediction_emails(mock_session, ["u1"], "Analyst", "analyst-slug", "SYM", "Stock")

    mock_adapter.send_notification.assert_awaited_once()
    call_args = mock_adapter.send_notification.call_args
    assert call_args[0][0] == "x@y.com"
    assert "Analyst" in call_args[0][1]


async def test_send_outcome_emails_no_verified_users() -> None:
    """When no users have verified email, no emails are sent."""
    from app.jobs.notifications import _send_outcome_emails

    mock_session = AsyncMock()
    outcome_result = MagicMock()
    outcome_result.scalar_one_or_none.return_value = "hit"
    user_result = MagicMock()
    user_result.scalars.return_value = MagicMock(all=lambda: [])
    mock_session.execute = AsyncMock(side_effect=[outcome_result, user_result])

    with (
        patch("app.core.config.get_settings") as mock_get,
        patch("app.integrations.email.resend_adapter.ResendAdapter") as mock_adapter_cls,
    ):
        mock_get.return_value = MagicMock(NOTIFICATION_EMAIL_ENABLED=True)
        mock_adapter = AsyncMock()
        mock_adapter_cls.return_value = mock_adapter

        await _send_outcome_emails(mock_session, ["u1"], "SYM", "Stock", "pid1")

    mock_adapter.send_notification.assert_not_awaited()
