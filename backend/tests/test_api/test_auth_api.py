"""Integration tests for auth API endpoints."""

import uuid
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_refresh_token
from tests.conftest import create_test_otp, create_test_user


def _auth_header(user_id: uuid.UUID, role: str = "user") -> dict[str, str]:
    token = create_access_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# OTP Send
# ---------------------------------------------------------------------------


@patch("app.services.auth.otp_send_limiter", new_callable=lambda: type("M", (), {"check": AsyncMock()}))
async def test_otp_send_email(mock_limiter: object, client: AsyncClient, db_session: AsyncSession) -> None:
    with patch("app.services.auth.ResendAdapter") as mock_adapter:
        mock_adapter.return_value.send_otp = AsyncMock(return_value=True)
        resp = await client.post(
            "/api/v1/auth/otp/send",
            json={"identifier": "test@example.com", "purpose": "login"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["identifier"] == "test@example.com"
    assert data["expires_in_seconds"] == 300


async def test_otp_send_invalid_identifier(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/v1/auth/otp/send",
        json={"identifier": "not-valid", "purpose": "login"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# OTP Verify
# ---------------------------------------------------------------------------


@patch("app.services.auth.otp_verify_limiter", new_callable=lambda: type("M", (), {"check": AsyncMock()}))
@patch("app.services.auth.store_refresh_token", new_callable=AsyncMock)
async def test_otp_verify_success(
    mock_store: AsyncMock, mock_limiter: object, client: AsyncClient, db_session: AsyncSession
) -> None:
    await create_test_otp(db_session, identifier="verify@example.com", code="654321")
    resp = await client.post(
        "/api/v1/auth/otp/verify",
        json={"identifier": "verify@example.com", "code": "654321", "purpose": "login"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["user"]["email"] == "verify@example.com"


@patch("app.services.auth.otp_verify_limiter", new_callable=lambda: type("M", (), {"check": AsyncMock()}))
async def test_otp_verify_wrong_code(mock_limiter: object, client: AsyncClient, db_session: AsyncSession) -> None:
    await create_test_otp(db_session, identifier="verify@example.com", code="654321")
    resp = await client.post(
        "/api/v1/auth/otp/verify",
        json={"identifier": "verify@example.com", "code": "000000", "purpose": "login"},
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------------
# Refresh
# ---------------------------------------------------------------------------


@patch("app.services.auth.store_refresh_token", new_callable=AsyncMock)
@patch("app.services.auth.revoke_refresh_token", new_callable=AsyncMock)
@patch("app.services.auth.is_refresh_token_valid", new_callable=AsyncMock, return_value=True)
async def test_refresh_endpoint(
    mock_valid: AsyncMock,
    mock_revoke: AsyncMock,
    mock_store: AsyncMock,
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    user = await create_test_user(db_session, email="refresh@example.com")
    token, jti = create_refresh_token(user.id, "user")

    resp = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": token},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_refresh_no_cookie(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------


@patch("app.services.auth.revoke_all_refresh_tokens", new_callable=AsyncMock)
async def test_logout(mock_revoke: AsyncMock, client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session, email="logout@example.com")
    resp = await client.post(
        "/api/v1/auth/logout",
        headers=_auth_header(user.id),
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Logged out successfully"


async def test_logout_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code in (401, 403)


# ---------------------------------------------------------------------------
# Me
# ---------------------------------------------------------------------------


async def test_get_me(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session, email="me@example.com", name="Me User")
    resp = await client.get("/api/v1/auth/me", headers=_auth_header(user.id))
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


async def test_update_me(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session, email="update-me@example.com")
    resp = await client.patch(
        "/api/v1/auth/me",
        json={"name": "New Name"},
        headers=_auth_header(user.id),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "New Name"
