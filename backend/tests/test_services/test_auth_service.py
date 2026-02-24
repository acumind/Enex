"""Tests for AuthService: OTP send/verify, Google login, refresh, logout, account linking."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.exceptions import HTTPException

from app.core.security import create_refresh_token
from app.schemas.auth import GoogleAuthRequest, OTPSendRequest, OTPVerifyRequest
from app.services.auth import AuthService
from tests.conftest import create_test_otp, create_test_user

# ---------------------------------------------------------------------------
# OTP Send
# ---------------------------------------------------------------------------


@patch("app.services.auth.otp_send_limiter", new_callable=lambda: type("M", (), {"check": AsyncMock()}))
async def test_send_otp_creates_otp_record(mock_limiter: MagicMock, db_session: AsyncSession) -> None:
    service = AuthService(db_session)
    service.email_adapter = AsyncMock()
    service.email_adapter.send_otp = AsyncMock(return_value=True)

    result = await service.send_otp(OTPSendRequest(identifier="user@example.com", purpose="login"))

    assert result.identifier == "user@example.com"
    assert result.expires_in_seconds == 300


@patch("app.services.auth.otp_send_limiter", new_callable=lambda: type("M", (), {"check": AsyncMock()}))
async def test_send_otp_phone(mock_limiter: MagicMock, db_session: AsyncSession) -> None:
    service = AuthService(db_session)
    service.sms_adapter = AsyncMock()
    service.sms_adapter.send_otp = AsyncMock(return_value=True)

    result = await service.send_otp(OTPSendRequest(identifier="+919876543210", purpose="login"))

    assert result.identifier == "+919876543210"
    service.sms_adapter.send_otp.assert_awaited_once()


@patch("app.services.auth.otp_send_limiter", new_callable=lambda: type("M", (), {"check": AsyncMock()}))
async def test_send_otp_cooldown(mock_limiter: MagicMock, db_session: AsyncSession) -> None:
    """Should reject if OTP sent recently (within cooldown window)."""
    await create_test_otp(db_session, identifier="user@example.com", code="111111")
    service = AuthService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.send_otp(OTPSendRequest(identifier="user@example.com", purpose="login"))
    assert exc_info.value.status_code == 429


# ---------------------------------------------------------------------------
# OTP Verify
# ---------------------------------------------------------------------------


@patch("app.services.auth.otp_verify_limiter", new_callable=lambda: type("M", (), {"check": AsyncMock()}))
@patch("app.services.auth.store_refresh_token", new_callable=AsyncMock)
async def test_verify_otp_success(mock_store: AsyncMock, mock_limiter: MagicMock, db_session: AsyncSession) -> None:
    await create_test_otp(db_session, identifier="user@example.com", code="654321")
    service = AuthService(db_session)

    result, refresh_tok, jti = await service.verify_otp(
        OTPVerifyRequest(identifier="user@example.com", code="654321", purpose="login")
    )

    assert result.access_token
    assert result.user.email == "user@example.com"
    assert result.user.is_email_verified is True
    assert refresh_tok
    assert jti


@patch("app.services.auth.otp_verify_limiter", new_callable=lambda: type("M", (), {"check": AsyncMock()}))
async def test_verify_otp_wrong_code(mock_limiter: MagicMock, db_session: AsyncSession) -> None:
    await create_test_otp(db_session, identifier="user@example.com", code="654321")
    service = AuthService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.verify_otp(OTPVerifyRequest(identifier="user@example.com", code="000000", purpose="login"))
    assert exc_info.value.status_code == 400
    assert "Invalid code" in str(exc_info.value.detail)


@patch("app.services.auth.otp_verify_limiter", new_callable=lambda: type("M", (), {"check": AsyncMock()}))
async def test_verify_otp_max_attempts(mock_limiter: MagicMock, db_session: AsyncSession) -> None:
    await create_test_otp(db_session, identifier="user@example.com", code="654321", attempts=3)
    service = AuthService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.verify_otp(OTPVerifyRequest(identifier="user@example.com", code="654321", purpose="login"))
    assert exc_info.value.status_code == 400
    assert "Too many incorrect attempts" in str(exc_info.value.detail)


@patch("app.services.auth.otp_verify_limiter", new_callable=lambda: type("M", (), {"check": AsyncMock()}))
async def test_verify_otp_no_valid_otp(mock_limiter: MagicMock, db_session: AsyncSession) -> None:
    service = AuthService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.verify_otp(OTPVerifyRequest(identifier="noone@example.com", code="123456", purpose="login"))
    assert exc_info.value.status_code == 400


@patch("app.services.auth.otp_verify_limiter", new_callable=lambda: type("M", (), {"check": AsyncMock()}))
@patch("app.services.auth.store_refresh_token", new_callable=AsyncMock)
async def test_verify_otp_links_existing_user(
    mock_store: AsyncMock, mock_limiter: MagicMock, db_session: AsyncSession
) -> None:
    """If a user with this email already exists, OTP verify should link to that user."""
    user = await create_test_user(db_session, email="existing@example.com")
    await create_test_otp(db_session, identifier="existing@example.com", code="654321")
    service = AuthService(db_session)

    result, _, _ = await service.verify_otp(
        OTPVerifyRequest(identifier="existing@example.com", code="654321", purpose="login")
    )
    assert result.user.id == user.id
    assert result.user.is_email_verified is True


@patch("app.services.auth.otp_verify_limiter", new_callable=lambda: type("M", (), {"check": AsyncMock()}))
@patch("app.services.auth.store_refresh_token", new_callable=AsyncMock)
async def test_verify_otp_phone_creates_user(
    mock_store: AsyncMock, mock_limiter: MagicMock, db_session: AsyncSession
) -> None:
    await create_test_otp(db_session, identifier="+919876543210", code="654321")
    service = AuthService(db_session)

    result, _, _ = await service.verify_otp(
        OTPVerifyRequest(identifier="+919876543210", code="654321", purpose="login")
    )
    assert result.user.phone == "+919876543210"
    assert result.user.is_phone_verified is True


# ---------------------------------------------------------------------------
# Google Login
# ---------------------------------------------------------------------------


@patch("app.services.auth.store_refresh_token", new_callable=AsyncMock)
async def test_google_login_success(mock_store: AsyncMock, db_session: AsyncSession) -> None:
    from app.integrations.oauth.google_verifier import GoogleUserInfo

    service = AuthService(db_session)
    service.google_verifier = AsyncMock()
    service.google_verifier.verify_id_token = AsyncMock(
        return_value=GoogleUserInfo(
            email="google@example.com",
            name="Google User",
            picture="https://photo.url/pic.jpg",
            google_id="goog123",
        )
    )

    result, refresh_tok, jti = await service.google_login(GoogleAuthRequest(id_token="fake-id-token"))
    assert result.user.email == "google@example.com"
    assert result.user.name == "Google User"
    assert "google" in result.user.auth_methods


@patch("app.services.auth.store_refresh_token", new_callable=AsyncMock)
async def test_google_login_links_existing_user(mock_store: AsyncMock, db_session: AsyncSession) -> None:
    from app.integrations.oauth.google_verifier import GoogleUserInfo

    user = await create_test_user(db_session, email="link@example.com", name="Existing")
    service = AuthService(db_session)
    service.google_verifier = AsyncMock()
    service.google_verifier.verify_id_token = AsyncMock(
        return_value=GoogleUserInfo(email="link@example.com", name="Google Name", picture=None, google_id="g456")
    )

    result, _, _ = await service.google_login(GoogleAuthRequest(id_token="tok"))
    assert result.user.id == user.id
    assert result.user.name == "Existing"  # keeps existing name


async def test_google_login_invalid_token(db_session: AsyncSession) -> None:
    service = AuthService(db_session)
    service.google_verifier = AsyncMock()
    service.google_verifier.verify_id_token = AsyncMock(return_value=None)
    service.google_verifier.verify_access_token = AsyncMock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        await service.google_login(GoogleAuthRequest(access_token="bad-token"))
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Refresh Token
# ---------------------------------------------------------------------------


@patch("app.services.auth.store_refresh_token", new_callable=AsyncMock)
@patch("app.services.auth.revoke_refresh_token", new_callable=AsyncMock)
@patch("app.services.auth.is_refresh_token_valid", new_callable=AsyncMock, return_value=True)
async def test_refresh_token_success(
    mock_valid: AsyncMock, mock_revoke: AsyncMock, mock_store: AsyncMock, db_session: AsyncSession
) -> None:
    user = await create_test_user(db_session, email="refresh@example.com")
    token, jti = create_refresh_token(user.id, "user")
    service = AuthService(db_session)

    result, new_refresh, new_jti = await service.refresh_access_token(token)
    assert result.access_token
    mock_revoke.assert_awaited_once_with(jti)
    mock_store.assert_awaited_once()


@patch("app.services.auth.is_refresh_token_valid", new_callable=AsyncMock, return_value=False)
async def test_refresh_token_revoked(mock_valid: AsyncMock, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session, email="revoked@example.com")
    token, _jti = create_refresh_token(user.id, "user")
    service = AuthService(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await service.refresh_access_token(token)
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


@patch("app.services.auth.revoke_all_refresh_tokens", new_callable=AsyncMock)
async def test_logout(mock_revoke_all: AsyncMock, db_session: AsyncSession) -> None:
    user_id = uuid.uuid4()
    service = AuthService(db_session)
    await service.logout(user_id)
    mock_revoke_all.assert_awaited_once_with(user_id)
