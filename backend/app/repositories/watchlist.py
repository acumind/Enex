"""Watchlist data access repository (composite PK — does not extend BaseRepository)."""

import uuid
from datetime import datetime

from sqlalchemy import and_, delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.engagement import UserWatchlist
from app.models.stock import Stock


class WatchlistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, user_id: uuid.UUID, stock_id: uuid.UUID) -> UserWatchlist:
        entry = UserWatchlist(user_id=user_id, stock_id=stock_id)
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def remove(self, user_id: uuid.UUID, stock_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            delete(UserWatchlist).where(and_(UserWatchlist.user_id == user_id, UserWatchlist.stock_id == stock_id))
        )
        await self.session.flush()
        return result.rowcount > 0  # type: ignore[union-attr]

    async def exists(self, user_id: uuid.UUID, stock_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(func.count())
            .select_from(UserWatchlist)
            .where(and_(UserWatchlist.user_id == user_id, UserWatchlist.stock_id == stock_id))
        )
        return result.scalar_one() > 0

    async def list_for_user(
        self,
        user_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[tuple[UserWatchlist, Stock]]:
        stmt = (
            select(UserWatchlist, Stock)
            .join(Stock, UserWatchlist.stock_id == Stock.id)
            .where(UserWatchlist.user_id == user_id)
            .order_by(UserWatchlist.created_at.desc())
        )
        if cursor is not None:
            stmt = stmt.where(UserWatchlist.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.all())

    async def count_for_user(self, user_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(UserWatchlist).where(UserWatchlist.user_id == user_id)
        )
        return result.scalar_one()

    async def list_users_watching_stock(self, stock_id: uuid.UUID) -> list[uuid.UUID]:
        result = await self.session.execute(select(UserWatchlist.user_id).where(UserWatchlist.stock_id == stock_id))
        return [row[0] for row in result.all()]
