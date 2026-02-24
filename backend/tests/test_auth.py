"""Tests for JWT token creation, verification, expired/invalid tokens."""

import uuid
from datetime import UTC, datetime, timedelta

import pytest
from jose import jwt

from app.core.security import create_access_token, create_refresh_token, verify_token


def test_create_access_token_returns_valid_jwt() -> None:
    user_id = uuid.uuid4()
    token = create_access_token(user_id, "admin")
    data = verify_token(token)
    assert data.user_id == user_id
    assert data.role == "admin"
    assert data.token_type == "access"


def test_create_refresh_token_returns_valid_jwt() -> None:
    user_id = uuid.uuid4()
    token, jti = create_refresh_token(user_id, "user")
    data = verify_token(token)
    assert data.user_id == user_id
    assert data.token_type == "refresh"
    assert data.role == "user"
    assert data.jti == jti
    assert jti  # non-empty


def test_verify_token_rejects_expired_token() -> None:
    from jose import JWTError

    from app.core.config import get_settings

    settings = get_settings()
    payload = {
        "sub": str(uuid.uuid4()),
        "role": "user",
        "type": "access",
        "exp": datetime.now(UTC) - timedelta(hours=1),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(JWTError):
        verify_token(token)


def test_verify_token_rejects_invalid_signature() -> None:
    from jose import JWTError

    payload = {
        "sub": str(uuid.uuid4()),
        "role": "user",
        "type": "access",
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    token = jwt.encode(payload, "wrong-secret", algorithm="HS256")
    with pytest.raises(JWTError):
        verify_token(token)


def test_verify_token_rejects_missing_subject() -> None:
    from jose import JWTError

    from app.core.config import get_settings

    settings = get_settings()
    payload = {
        "role": "user",
        "type": "access",
        "exp": datetime.now(UTC) + timedelta(hours=1),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    with pytest.raises(JWTError, match="Token missing subject claim"):
        verify_token(token)
