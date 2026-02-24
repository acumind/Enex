"""JWT token creation and verification primitives. No FastAPI imports."""

import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import get_settings


class TokenData(BaseModel):
    user_id: uuid.UUID
    role: str
    token_type: str  # "access" or "refresh"


def create_access_token(user_id: uuid.UUID, role: str) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(hours=settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return str(jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM))


def create_refresh_token(user_id: uuid.UUID) -> str:
    settings = get_settings()
    expire = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": expire,
    }
    return str(jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM))


def verify_token(token: str) -> TokenData:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise

    sub = payload.get("sub")
    role = payload.get("role", "user")
    token_type = payload.get("type", "access")

    if sub is None:
        raise JWTError("Token missing subject claim")

    return TokenData(user_id=uuid.UUID(sub), role=role, token_type=token_type)
