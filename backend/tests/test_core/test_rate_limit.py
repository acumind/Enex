"""Tests for RateLimiter — Redis pipeline, 429 enforcement, fail-open behavior."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.exceptions import HTTPException

from app.core.rate_limit import RateLimiter


def _mock_redis(pipe_execute_return=None):
    """Create a mock redis client with sync pipeline() and async pipeline methods."""
    mock_pipe = AsyncMock()
    if pipe_execute_return is not None:
        mock_pipe.execute.return_value = pipe_execute_return

    mock_redis = MagicMock()
    mock_redis.pipeline.return_value = mock_pipe
    mock_redis.aclose = AsyncMock()
    return mock_redis, mock_pipe


async def test_check_allows_under_limit() -> None:
    """Request count under limit → no exception."""
    limiter = RateLimiter("test", max_requests=5, window_seconds=60)

    mock_redis, mock_pipe = _mock_redis(pipe_execute_return=[3])

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        # Should not raise
        await limiter.check("user-123")

    mock_pipe.incr.assert_awaited_once_with("rate_limit:test:user-123")
    mock_pipe.expire.assert_awaited_once_with("rate_limit:test:user-123", 60)
    mock_redis.aclose.assert_awaited_once()


async def test_check_raises_429_when_over_limit() -> None:
    """Request count exceeds limit → HTTPException 429."""
    limiter = RateLimiter("test", max_requests=5, window_seconds=60)

    mock_redis, _ = _mock_redis(pipe_execute_return=[6])

    with patch("redis.asyncio.from_url", return_value=mock_redis), pytest.raises(HTTPException) as exc_info:
        await limiter.check("user-123")

    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail


async def test_check_raises_429_at_exact_boundary() -> None:
    """Request count exactly at limit → allowed. One over → 429."""
    limiter = RateLimiter("test", max_requests=5, window_seconds=60)

    mock_redis, _ = _mock_redis(pipe_execute_return=[5])

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        # count == max_requests → should NOT raise (only > raises)
        await limiter.check("user-123")


async def test_check_fails_open_on_redis_connection_error() -> None:
    """If Redis is unreachable, allow the request (fail-open)."""
    limiter = RateLimiter("test", max_requests=5, window_seconds=60)

    with patch("redis.asyncio.from_url", side_effect=ConnectionError("Redis down")):
        # Should NOT raise — fail open
        await limiter.check("user-123")


async def test_check_fails_open_on_redis_timeout() -> None:
    """If Redis times out, allow the request (fail-open)."""
    limiter = RateLimiter("test", max_requests=5, window_seconds=60)

    mock_pipe = AsyncMock()
    mock_pipe.execute.side_effect = TimeoutError("Redis timeout")

    mock_redis = MagicMock()
    mock_redis.pipeline.return_value = mock_pipe
    mock_redis.aclose = AsyncMock()

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        # Should NOT raise — fail open
        await limiter.check("user-123")

    # Redis connection still closed
    mock_redis.aclose.assert_awaited_once()


async def test_check_reraises_http_exception() -> None:
    """HTTPException (429) should NOT be swallowed by the fail-open catch."""
    limiter = RateLimiter("test", max_requests=1, window_seconds=60)

    mock_redis, _ = _mock_redis(pipe_execute_return=[10])

    with patch("redis.asyncio.from_url", return_value=mock_redis), pytest.raises(HTTPException) as exc_info:
        await limiter.check("user-123")

    # Confirms the HTTPException re-raise path works
    assert exc_info.value.status_code == 429


def test_preconfigured_limiters() -> None:
    """Verify the module-level limiter instances have correct config."""
    from app.core.rate_limit import bulk_extract_limiter, extract_limiter, prediction_submit_limiter

    assert extract_limiter.key_prefix == "extract"
    assert extract_limiter.max_requests == 10
    assert extract_limiter.window_seconds == 3600

    assert prediction_submit_limiter.key_prefix == "prediction_submit"
    assert prediction_submit_limiter.max_requests == 20
    assert prediction_submit_limiter.window_seconds == 86400

    assert bulk_extract_limiter.key_prefix == "bulk_extract"
    assert bulk_extract_limiter.max_requests == 5
    assert bulk_extract_limiter.window_seconds == 3600
