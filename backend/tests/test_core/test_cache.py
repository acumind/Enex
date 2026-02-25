"""Tests for Redis caching utility — get/set, decorator, fail-open behavior."""

from unittest.mock import AsyncMock, MagicMock, patch

from pydantic import BaseModel

from app.core.cache import cache_get, cache_set, cached_response


async def test_cache_miss_returns_none() -> None:
    """cache_get returns None when key doesn't exist."""
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.aclose = AsyncMock()

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        result = await cache_get("missing_key")

    assert result is None


async def test_cache_set_get_roundtrip() -> None:
    """cache_set stores value, cache_get retrieves it."""
    store: dict[str, str] = {}

    async def mock_set(key: str, value: str, ex: int) -> None:
        store[key] = value

    async def mock_get(key: str) -> str | None:
        return store.get(key)

    mock_redis = MagicMock()
    mock_redis.set = AsyncMock(side_effect=mock_set)
    mock_redis.get = AsyncMock(side_effect=mock_get)
    mock_redis.aclose = AsyncMock()

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        await cache_set("test_key", '{"hello": "world"}', 60)
        result = await cache_get("test_key")

    assert result == '{"hello": "world"}'


async def test_cache_get_fails_open_on_redis_error() -> None:
    """cache_get returns None when Redis raises an error."""
    with patch("redis.asyncio.from_url", side_effect=ConnectionError("Redis down")):
        result = await cache_get("any_key")

    assert result is None


async def test_cache_set_fails_silently_on_redis_error() -> None:
    """cache_set does not raise when Redis is unavailable."""
    with patch("redis.asyncio.from_url", side_effect=ConnectionError("Redis down")):
        # Should not raise
        await cache_set("any_key", "value", 60)


async def test_decorator_caches_pydantic_model() -> None:
    """@cached_response caches and deserializes Pydantic models."""

    class MyModel(BaseModel):
        count: int
        name: str

    call_count = 0

    class FakeService:
        @cached_response("test", ttl_seconds=60)
        async def get_data(self) -> MyModel:
            nonlocal call_count
            call_count += 1
            return MyModel(count=42, name="test")

    store: dict[str, str] = {}

    async def mock_get(key: str) -> str | None:
        return store.get(key)

    async def mock_set(key: str, value: str, ex: int) -> None:
        store[key] = value

    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(side_effect=mock_get)
    mock_redis.set = AsyncMock(side_effect=mock_set)
    mock_redis.aclose = AsyncMock()

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        svc = FakeService()
        result1 = await svc.get_data()
        result2 = await svc.get_data()

    assert result1.count == 42
    assert result2.count == 42
    assert call_count == 1  # Second call served from cache


async def test_decorator_different_args_different_keys() -> None:
    """Different arguments produce different cache keys."""

    class MyModel(BaseModel):
        value: str

    class FakeService:
        @cached_response("test", ttl_seconds=60)
        async def get_data(self, key: str) -> MyModel:
            return MyModel(value=key)

    store: dict[str, str] = {}

    async def mock_get(key: str) -> str | None:
        return store.get(key)

    async def mock_set(key: str, value: str, ex: int) -> None:
        store[key] = value

    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(side_effect=mock_get)
    mock_redis.set = AsyncMock(side_effect=mock_set)
    mock_redis.aclose = AsyncMock()

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        svc = FakeService()
        r1 = await svc.get_data("alpha")
        r2 = await svc.get_data("beta")

    assert r1.value == "alpha"
    assert r2.value == "beta"
    # Two distinct keys stored
    assert len(store) == 2


async def test_decorator_fails_open_when_redis_unavailable() -> None:
    """Decorator executes function normally when Redis is down."""

    class MyModel(BaseModel):
        value: int

    class FakeService:
        @cached_response("test", ttl_seconds=60)
        async def get_data(self) -> MyModel:
            return MyModel(value=99)

    with patch("redis.asyncio.from_url", side_effect=ConnectionError("Redis down")):
        svc = FakeService()
        result = await svc.get_data()

    assert result.value == 99
