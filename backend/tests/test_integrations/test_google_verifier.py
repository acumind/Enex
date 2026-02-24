"""Tests for GoogleVerifier: ID token, access token, invalid, audience mismatch."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx


@patch("app.integrations.oauth.google_verifier.get_settings")
@patch("app.integrations.oauth.google_verifier.httpx.AsyncClient")
async def test_verify_id_token_success(mock_client_cls: MagicMock, mock_settings: MagicMock) -> None:
    mock_settings.return_value = MagicMock(GOOGLE_CLIENT_ID="test-client-id")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "aud": "test-client-id",
        "email": "user@gmail.com",
        "name": "Test User",
        "picture": "https://photo.url/pic.jpg",
        "sub": "google123",
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    from app.integrations.oauth.google_verifier import GoogleVerifier

    verifier = GoogleVerifier()
    result = await verifier.verify_id_token("fake-id-token")

    assert result is not None
    assert result.email == "user@gmail.com"
    assert result.name == "Test User"
    assert result.google_id == "google123"


@patch("app.integrations.oauth.google_verifier.get_settings")
@patch("app.integrations.oauth.google_verifier.httpx.AsyncClient")
async def test_verify_id_token_audience_mismatch(mock_client_cls: MagicMock, mock_settings: MagicMock) -> None:
    mock_settings.return_value = MagicMock(GOOGLE_CLIENT_ID="test-client-id")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "aud": "wrong-client-id",
        "email": "user@gmail.com",
        "sub": "google123",
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    from app.integrations.oauth.google_verifier import GoogleVerifier

    verifier = GoogleVerifier()
    result = await verifier.verify_id_token("fake-id-token")
    assert result is None


@patch("app.integrations.oauth.google_verifier.httpx.AsyncClient")
async def test_verify_access_token_success(mock_client_cls: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "email": "user@gmail.com",
        "name": "Access User",
        "picture": None,
        "sub": "google456",
    }
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    from app.integrations.oauth.google_verifier import GoogleVerifier

    verifier = GoogleVerifier()
    result = await verifier.verify_access_token("fake-access-token")
    assert result is not None
    assert result.email == "user@gmail.com"


@patch("app.integrations.oauth.google_verifier.httpx.AsyncClient")
async def test_verify_access_token_failure(mock_client_cls: MagicMock) -> None:
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    from app.integrations.oauth.google_verifier import GoogleVerifier

    verifier = GoogleVerifier()
    result = await verifier.verify_access_token("bad-token")
    assert result is None


@patch("app.integrations.oauth.google_verifier.httpx.AsyncClient")
async def test_verify_access_token_network_error(mock_client_cls: MagicMock) -> None:
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=httpx.ConnectError("Connection refused"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    from app.integrations.oauth.google_verifier import GoogleVerifier

    verifier = GoogleVerifier()
    result = await verifier.verify_access_token("any-token")
    assert result is None
