"""Tests for MSG91Adapter: success, API error, missing key."""

from unittest.mock import AsyncMock, MagicMock, patch


@patch("app.integrations.sms.msg91_adapter.get_settings")
async def test_returns_false_when_auth_key_empty(mock_settings: MagicMock) -> None:
    mock_settings.return_value = MagicMock(MSG91_AUTH_KEY="")
    from app.integrations.sms.msg91_adapter import MSG91Adapter

    adapter = MSG91Adapter()
    result = await adapter.send_otp("+919876543210", "123456")
    assert result is False


@patch("app.integrations.sms.msg91_adapter.get_settings")
@patch("app.integrations.sms.msg91_adapter.httpx.AsyncClient")
async def test_send_otp_success(mock_client_cls: MagicMock, mock_settings: MagicMock) -> None:
    mock_settings.return_value = MagicMock(
        MSG91_AUTH_KEY="test_key",
        MSG91_TEMPLATE_ID="tpl_123",
        MSG91_SENDER_ID="ENEXIN",
    )
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    from app.integrations.sms.msg91_adapter import MSG91Adapter

    adapter = MSG91Adapter()
    result = await adapter.send_otp("+919876543210", "123456")
    assert result is True
    # Verify phone stripped of '+' prefix
    call_kwargs = mock_client.post.call_args
    assert call_kwargs[1]["json"]["mobile"] == "919876543210"


@patch("app.integrations.sms.msg91_adapter.get_settings")
@patch("app.integrations.sms.msg91_adapter.httpx.AsyncClient")
async def test_send_otp_api_error(mock_client_cls: MagicMock, mock_settings: MagicMock) -> None:
    mock_settings.return_value = MagicMock(
        MSG91_AUTH_KEY="test_key",
        MSG91_TEMPLATE_ID="tpl_123",
        MSG91_SENDER_ID="ENEXIN",
    )
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal error"
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    from app.integrations.sms.msg91_adapter import MSG91Adapter

    adapter = MSG91Adapter()
    result = await adapter.send_otp("+919876543210", "123456")
    assert result is False
