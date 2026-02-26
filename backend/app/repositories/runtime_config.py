"""Runtime configuration repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.runtime_config import RuntimeConfig


class RuntimeConfigRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_key(self, key: str) -> RuntimeConfig | None:
        return await self.session.get(RuntimeConfig, key)

    async def list_all(self) -> list[RuntimeConfig]:
        result = await self.session.execute(select(RuntimeConfig).order_by(RuntimeConfig.key))
        return list(result.scalars().all())

    async def upsert(self, key: str, value: str, updated_by: uuid.UUID | None = None) -> RuntimeConfig:
        existing = await self.get_by_key(key)
        if existing:
            existing.value = value
            existing.updated_by = updated_by
            await self.session.flush()
            await self.session.refresh(existing)
            return existing
        config = RuntimeConfig(key=key, value=value, updated_by=updated_by)
        self.session.add(config)
        await self.session.flush()
        return config
