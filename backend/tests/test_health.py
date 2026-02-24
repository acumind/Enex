from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


async def test_health_returns_200(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["db"] == "ok"
    assert data["redis"] == "ok"
    assert data["version"] == "0.1.0"


async def test_health_response_shape(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    data = response.json()
    assert set(data.keys()) == {"status", "db", "redis", "version"}


async def test_health_degraded_when_redis_down(client: AsyncClient) -> None:
    """Redis failure → status=degraded, redis=error, HTTP 503."""
    mock_redis = AsyncMock()
    mock_redis.ping.side_effect = ConnectionError("Redis down")

    with patch("redis.asyncio.from_url", return_value=mock_redis):
        response = await client.get("/api/v1/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["db"] == "ok"
    assert data["redis"] == "error"


async def test_health_degraded_when_db_down(client: AsyncClient) -> None:
    """DB failure → status=degraded, db=error, HTTP 503."""
    with patch("sqlalchemy.ext.asyncio.AsyncSession.execute", side_effect=Exception("DB down")):
        response = await client.get("/api/v1/health")

    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "degraded"
    assert data["db"] == "error"
