"""Runtime configuration service with Redis caching."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_get, cache_set
from app.repositories.runtime_config import RuntimeConfigRepository
from app.schemas.runtime_config import RuntimeConfigResponse


class RuntimeConfigService:
    CACHE_PREFIX = "enex:config:"
    CACHE_TTL = 60  # seconds

    def __init__(self, session: AsyncSession) -> None:
        self.repo = RuntimeConfigRepository(session)

    async def get(self, key: str, default: str | None = None) -> str | None:
        cached = await cache_get(f"{self.CACHE_PREFIX}{key}")
        if cached is not None:
            return cached

        config = await self.repo.get_by_key(key)
        if config is None:
            return default

        await cache_set(f"{self.CACHE_PREFIX}{key}", config.value, self.CACHE_TTL)
        return config.value

    async def get_bool(self, key: str, default: bool = False) -> bool:
        value = await self.get(key)
        if value is None:
            return default
        return value.lower() in ("true", "1", "yes")

    async def set(self, key: str, value: str, updated_by: uuid.UUID | None = None) -> RuntimeConfigResponse:
        config = await self.repo.upsert(key, value, updated_by)
        # Invalidate cache by overwriting with new value
        await cache_set(f"{self.CACHE_PREFIX}{key}", value, self.CACHE_TTL)
        return RuntimeConfigResponse.model_validate(config)

    async def list_all(self) -> list[RuntimeConfigResponse]:
        configs = await self.repo.list_all()
        return [RuntimeConfigResponse.model_validate(c) for c in configs]
