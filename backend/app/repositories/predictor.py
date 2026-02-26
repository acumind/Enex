"""Predictor data access repository."""

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.predictor import Predictor
from app.repositories.base import BaseRepository


class PredictorRepository(BaseRepository[Predictor]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Predictor)

    async def get_by_slug(self, slug: str) -> Predictor | None:
        result = await self.session.execute(select(Predictor).where(Predictor.slug == slug))
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        result = await self.session.execute(select(Predictor.id).where(Predictor.slug == slug).limit(1))
        return result.scalar_one_or_none() is not None

    async def list_by_type(
        self,
        predictor_type: str,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[Predictor]:
        stmt = select(Predictor).where(Predictor.type == predictor_type).order_by(Predictor.created_at.desc())
        if cursor is not None:
            stmt = stmt.where(Predictor.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def search(self, query: str, *, limit: int = 10) -> list[Predictor]:
        pattern = f"%{query}%"
        stmt = (
            select(Predictor)
            .where((Predictor.name.ilike(pattern)) | (Predictor.slug.ilike(pattern)))
            .order_by(Predictor.name)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(
        self,
        *,
        search: str | None = None,
        type_filter: str | None = None,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[Predictor]:
        stmt = select(Predictor).order_by(Predictor.created_at.desc())
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(Predictor.name.ilike(pattern))
        if type_filter:
            stmt = stmt.where(Predictor.type == type_filter)
        if cursor is not None:
            stmt = stmt.where(Predictor.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_members(self, parent_id: uuid.UUID) -> list[Predictor]:
        result = await self.session.execute(
            select(Predictor).where(Predictor.parent_id == parent_id).order_by(Predictor.name)
        )
        return list(result.scalars().all())
