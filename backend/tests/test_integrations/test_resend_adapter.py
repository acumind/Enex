"""Tests for ResendAdapter: success, API error, missing key."""

from unittest.mock import AsyncMock, MagicMock, patch


@patch("app.integrations.email.resend_adapter.get_settings")
async def test_returns_false_when_api_key_empty(mock_settings: MagicMock) -> None:
    mock_settings.return_value = MagicMock(RESEND_API_KEY="")
    from app.integrations.email.resend_adapter import ResendAdapter

    adapter = ResendAdapter()
    result = await adapter.send_otp("test@example.com", "123456")
    assert result is False


@patch("app.integrations.email.resend_adapter.get_settings")
async def test_send_notification_returns_false_when_key_empty(mock_settings: MagicMock) -> None:
    mock_settings.return_value = MagicMock(RESEND_API_KEY="")
    from app.integrations.email.resend_adapter import ResendAdapter

    adapter = ResendAdapter()
    result = await adapter.send_notification("test@example.com", "Subject", "<p>body</p>")
    assert result is False


@patch("app.integrations.email.resend_adapter.get_settings")
@patch("app.integrations.email.resend_adapter.httpx.AsyncClient")
async def test_send_notification_success(mock_client_cls: MagicMock, mock_settings: MagicMock) -> None:
    mock_settings.return_value = MagicMock(RESEND_API_KEY="re_test_key", RESEND_FROM_EMAIL="noreply@enex.in")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    from app.integrations.email.resend_adapter import ResendAdapter

    adapter = ResendAdapter()
    result = await adapter.send_notification("test@example.com", "New prediction", "<p>Hello</p>")
    assert result is True


@patch("app.integrations.email.resend_adapter.get_settings")
@patch("app.integrations.email.resend_adapter.httpx.AsyncClient")
async def test_send_notification_api_error(mock_client_cls: MagicMock, mock_settings: MagicMock) -> None:
    mock_settings.return_value = MagicMock(RESEND_API_KEY="re_test_key", RESEND_FROM_EMAIL="noreply@enex.in")
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    from app.integrations.email.resend_adapter import ResendAdapter

    adapter = ResendAdapter()
    result = await adapter.send_notification("test@example.com", "Subject", "<p>body</p>")
    assert result is False


@patch("app.integrations.email.resend_adapter.get_settings")
@patch("app.integrations.email.resend_adapter.httpx.AsyncClient")
async def test_send_otp_success(mock_client_cls: MagicMock, mock_settings: MagicMock) -> None:
    mock_settings.return_value = MagicMock(RESEND_API_KEY="re_test_key", RESEND_FROM_EMAIL="noreply@enex.in")
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    from app.integrations.email.resend_adapter import ResendAdapter

    adapter = ResendAdapter()
    result = await adapter.send_otp("test@example.com", "123456")
    assert result is True


@patch("app.integrations.email.resend_adapter.get_settings")
@patch("app.integrations.email.resend_adapter.httpx.AsyncClient")
async def test_send_otp_api_error(mock_client_cls: MagicMock, mock_settings: MagicMock) -> None:
    mock_settings.return_value = MagicMock(RESEND_API_KEY="re_test_key", RESEND_FROM_EMAIL="noreply@enex.in")
    mock_response = MagicMock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    from app.integrations.email.resend_adapter import ResendAdapter

    adapter = ResendAdapter()
    result = await adapter.send_otp("test@example.com", "123456")
    assert result is False
