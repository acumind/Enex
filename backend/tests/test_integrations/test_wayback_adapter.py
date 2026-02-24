"""Tests for WaybackAdapter: disabled mode, success, and failure scenarios."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@patch("app.integrations.archive.wayback_adapter.get_settings")
async def test_returns_none_when_disabled(mock_get_settings: MagicMock) -> None:
    """When WAYBACK_ARCHIVAL_ENABLED is False, save_url should return None immediately."""
    settings = MagicMock()
    settings.WAYBACK_ARCHIVAL_ENABLED = False
    settings.WAYBACK_TIMEOUT_SECONDS = 10
    mock_get_settings.return_value = settings

    from app.integrations.archive.wayback_adapter import WaybackAdapter

    adapter = WaybackAdapter()
    result = await adapter.save_url("https://example.com/article")

    assert result is None


@patch("app.integrations.archive.wayback_adapter.get_settings")
@patch("app.integrations.archive.wayback_adapter.httpx.AsyncClient")
async def test_returns_snapshot_url_on_success(
    mock_async_client_cls: MagicMock, mock_get_settings: MagicMock
) -> None:
    """On 200 with a content-location header, return the full archive URL."""
    settings = MagicMock()
    settings.WAYBACK_ARCHIVAL_ENABLED = True
    settings.WAYBACK_TIMEOUT_SECONDS = 10
    mock_get_settings.return_value = settings

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-location": "/web/20260224120000/https://example.com/article"}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    from app.integrations.archive.wayback_adapter import WaybackAdapter

    adapter = WaybackAdapter()
    result = await adapter.save_url("https://example.com/article")

    assert result == "https://web.archive.org/web/20260224120000/https://example.com/article"
    mock_client.post.assert_awaited_once_with(
        "https://web.archive.org/save/https://example.com/article",
        follow_redirects=True,
    )


@patch("app.integrations.archive.wayback_adapter.get_settings")
@patch("app.integrations.archive.wayback_adapter.httpx.AsyncClient")
async def test_returns_fallback_url_when_no_content_location(
    mock_async_client_cls: MagicMock, mock_get_settings: MagicMock
) -> None:
    """On 200 without content-location or location header, return the fallback latest URL."""
    settings = MagicMock()
    settings.WAYBACK_ARCHIVAL_ENABLED = True
    settings.WAYBACK_TIMEOUT_SECONDS = 10
    mock_get_settings.return_value = settings

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}  # No location headers

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    from app.integrations.archive.wayback_adapter import WaybackAdapter

    adapter = WaybackAdapter()
    result = await adapter.save_url("https://example.com/article")

    assert result == "https://web.archive.org/web/latest/https://example.com/article"


@patch("app.integrations.archive.wayback_adapter.get_settings")
@patch("app.integrations.archive.wayback_adapter.httpx.AsyncClient")
async def test_returns_none_on_server_error(
    mock_async_client_cls: MagicMock, mock_get_settings: MagicMock
) -> None:
    """On a 500 status code, return None."""
    settings = MagicMock()
    settings.WAYBACK_ARCHIVAL_ENABLED = True
    settings.WAYBACK_TIMEOUT_SECONDS = 10
    mock_get_settings.return_value = settings

    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.headers = {}

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    from app.integrations.archive.wayback_adapter import WaybackAdapter

    adapter = WaybackAdapter()
    result = await adapter.save_url("https://example.com/article")

    assert result is None


@patch("app.integrations.archive.wayback_adapter.get_settings")
@patch("app.integrations.archive.wayback_adapter.httpx.AsyncClient")
async def test_returns_none_on_timeout(
    mock_async_client_cls: MagicMock, mock_get_settings: MagicMock
) -> None:
    """On a timeout exception, return None gracefully."""
    settings = MagicMock()
    settings.WAYBACK_ARCHIVAL_ENABLED = True
    settings.WAYBACK_TIMEOUT_SECONDS = 10
    mock_get_settings.return_value = settings

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("Connection timed out"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    from app.integrations.archive.wayback_adapter import WaybackAdapter

    adapter = WaybackAdapter()
    result = await adapter.save_url("https://example.com/article")

    assert result is None


@patch("app.integrations.archive.wayback_adapter.get_settings")
@patch("app.integrations.archive.wayback_adapter.httpx.AsyncClient")
async def test_returns_none_on_connection_error(
    mock_async_client_cls: MagicMock, mock_get_settings: MagicMock
) -> None:
    """On a connection error, return None gracefully."""
    settings = MagicMock()
    settings.WAYBACK_ARCHIVAL_ENABLED = True
    settings.WAYBACK_TIMEOUT_SECONDS = 10
    mock_get_settings.return_value = settings

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(side_effect=httpx.ConnectError("Failed to connect"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_async_client_cls.return_value = mock_client

    from app.integrations.archive.wayback_adapter import WaybackAdapter

    adapter = WaybackAdapter()
    result = await adapter.save_url("https://example.com/article")

    assert result is None
