"""JWT token creation and verification primitives. No FastAPI imports."""

import hashlib
import hmac
import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from pydantic import BaseModel

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TokenData(BaseModel):
    user_id: uuid.UUID
    role: str
    token_type: str  # "access" or "refresh"
    jti: str | None = None


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


def create_refresh_token(user_id: uuid.UUID, role: str) -> tuple[str, str]:
    """Create a refresh token with a unique JTI. Returns (token, jti)."""
    settings = get_settings()
    jti = uuid.uuid4().hex
    expire = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "role": role,
        "type": "refresh",
        "jti": jti,
        "exp": expire,
    }
    token = str(jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM))
    return token, jti


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
    jti = payload.get("jti")

    if sub is None:
        raise JWTError("Token missing subject claim")

    return TokenData(user_id=uuid.UUID(sub), role=role, token_type=token_type, jti=jti)


# ---------------------------------------------------------------------------
# OTP helpers
# ---------------------------------------------------------------------------


def generate_otp(length: int = 6) -> str:
    """Generate a cryptographically secure numeric OTP."""
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_otp(code: str) -> str:
    """SHA-256 hash of the OTP code (hex digest)."""
    return hashlib.sha256(code.encode()).hexdigest()


def verify_otp_hash(code: str, hashed: str) -> bool:
    """Constant-time comparison of OTP against its hash."""
    return hmac.compare_digest(hash_otp(code), hashed)


# ---------------------------------------------------------------------------
# Redis refresh-token allowlist (fail-closed)
# ---------------------------------------------------------------------------

_REFRESH_KEY_PREFIX = "refresh_token:"
_USER_TOKENS_KEY_PREFIX = "user_refresh_tokens:"


async def store_refresh_token(user_id: uuid.UUID, jti: str, expires_days: int | None = None) -> None:
    """Store a refresh token JTI in Redis allowlist."""
    import redis.asyncio as aioredis

    settings = get_settings()
    if expires_days is None:
        expires_days = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    ttl = expires_days * 86400

    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        pipe = r.pipeline()
        # Store individual JTI with TTL
        await pipe.set(f"{_REFRESH_KEY_PREFIX}{jti}", str(user_id), ex=ttl)
        # Track JTI in user's set (for revoke-all)
        user_key = f"{_USER_TOKENS_KEY_PREFIX}{user_id}"
        await pipe.sadd(user_key, jti)
        await pipe.expire(user_key, ttl)
        await pipe.execute()
    finally:
        await r.aclose()


async def is_refresh_token_valid(jti: str) -> bool:
    """Check if a refresh token JTI is in the allowlist. Fail-closed: returns False on Redis errors."""
    import redis.asyncio as aioredis

    settings = get_settings()
    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        try:
            result = await r.exists(f"{_REFRESH_KEY_PREFIX}{jti}")
            return bool(result)
        finally:
            await r.aclose()
    except Exception:
        logger.error("Redis unavailable for refresh token check, denying request (fail-closed)")
        return False


async def revoke_refresh_token(jti: str) -> None:
    """Remove a single refresh token JTI from Redis."""
    import redis.asyncio as aioredis

    settings = get_settings()
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        await r.delete(f"{_REFRESH_KEY_PREFIX}{jti}")
    finally:
        await r.aclose()


async def revoke_all_refresh_tokens(user_id: uuid.UUID) -> None:
    """Remove all refresh tokens for a user from Redis."""
    import redis.asyncio as aioredis

    settings = get_settings()
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        user_key = f"{_USER_TOKENS_KEY_PREFIX}{user_id}"
        jtis = await r.smembers(user_key)
        if jtis:
            pipe = r.pipeline()
            for jti in jtis:
                await pipe.delete(f"{_REFRESH_KEY_PREFIX}{jti}")
            await pipe.delete(user_key)
            await pipe.execute()
    finally:
        await r.aclose()
