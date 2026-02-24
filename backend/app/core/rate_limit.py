"""Redis-backed rate limiter with FastAPI dependency integration."""

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, Request
from starlette import status
from starlette.exceptions import HTTPException

from app.core.auth import get_current_user
from app.core.config import get_settings
from app.models.user import User

logger = logging.getLogger(__name__)


class RateLimiter:
    def __init__(self, key_prefix: str, max_requests: int, window_seconds: int) -> None:
        self.key_prefix = key_prefix
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def check(self, identifier: str) -> None:
        """Check rate limit. Raises HTTPException(429) if exceeded. Fails open on Redis errors."""
        import redis.asyncio as aioredis

        settings = get_settings()
        key = f"rate_limit:{self.key_prefix}:{identifier}"

        try:
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            try:
                pipe = r.pipeline()
                await pipe.incr(key)
                await pipe.expire(key, self.window_seconds)
                results = await pipe.execute()
                count = results[0]

                if count > self.max_requests:
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Rate limit exceeded. Max {self.max_requests} requests per {self.window_seconds}s.",
                    )
            finally:
                await r.aclose()
        except HTTPException:
            raise
        except Exception:
            logger.warning("Redis rate limit check failed, allowing request (fail-open)")

    def dependency(self) -> Callable[..., Coroutine[Any, Any, None]]:
        """Return a FastAPI dependency that enforces this rate limit for the current user."""
        limiter = self

        async def _check_rate_limit(
            request: Request,
            user: User = Depends(get_current_user),
        ) -> None:
            await limiter.check(str(user.id))

        return _check_rate_limit


# Pre-configured limiters
extract_limiter = RateLimiter("extract", max_requests=10, window_seconds=3600)
prediction_submit_limiter = RateLimiter("prediction_submit", max_requests=20, window_seconds=86400)
bulk_extract_limiter = RateLimiter("bulk_extract", max_requests=5, window_seconds=3600)
