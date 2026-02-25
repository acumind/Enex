"""Redis TTL caching utility with fail-open decorator for async service methods."""

import functools
import hashlib
import json
import logging
from collections.abc import Callable
from typing import Any

from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def cache_get(key: str) -> str | None:
    """Get a value from Redis. Returns None on miss or error (fail-open)."""
    import redis.asyncio as aioredis

    try:
        r = aioredis.from_url(get_settings().REDIS_URL, decode_responses=True)
        try:
            return await r.get(key)
        finally:
            await r.aclose()
    except Exception:
        logger.warning("Redis cache_get failed for key=%s, returning None (fail-open)", key)
        return None


async def cache_set(key: str, value: str, ttl: int) -> None:
    """Set a value in Redis with TTL. Fails silently on error (fail-open)."""
    import redis.asyncio as aioredis

    try:
        r = aioredis.from_url(get_settings().REDIS_URL, decode_responses=True)
        try:
            await r.set(key, value, ex=ttl)
        finally:
            await r.aclose()
    except Exception:
        logger.warning("Redis cache_set failed for key=%s (fail-open)", key)


def cached_response(key_prefix: str, ttl_seconds: int) -> Callable[..., Any]:
    """Decorator for async methods that caches Pydantic model responses in Redis.

    - Builds cache key from prefix + MD5 of serialized args
    - Serializes via model_dump_json(), deserializes via model_validate_json()
    - Fail-open: Redis errors are logged, function always executes on miss
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Build cache key: skip `self` (first arg) for bound methods
            key_parts = str(args[1:]) + str(sorted(kwargs.items()))
            key_hash = hashlib.md5(key_parts.encode()).hexdigest()  # noqa: S324
            cache_key = f"cache:{key_prefix}:{key_hash}"

            # Try cache hit
            cached = await cache_get(cache_key)
            if cached is not None:
                # Determine the return type from annotations
                return_type = func.__annotations__.get("return")
                if return_type and hasattr(return_type, "model_validate_json"):
                    return return_type.model_validate_json(cached)
                return json.loads(cached)

            # Cache miss — execute function
            result = await func(*args, **kwargs)

            # Store in cache
            serialized = result.model_dump_json() if hasattr(result, "model_dump_json") else json.dumps(result)
            await cache_set(cache_key, serialized, ttl_seconds)

            return result

        return wrapper

    return decorator
