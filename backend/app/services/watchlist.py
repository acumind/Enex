"""Watchlist business logic."""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.repositories.stock import StockRepository
from app.repositories.watchlist import WatchlistRepository
from app.schemas.common import PaginatedResponse
from app.schemas.engagement import WatchlistItemEnriched


class WatchlistService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = WatchlistRepository(session)
        self.stock_repo = StockRepository(session)

    async def add(self, user_id: uuid.UUID, stock_id: uuid.UUID) -> None:
        stock = await self.stock_repo.get_by_id(stock_id)
        if stock is None:
            raise NotFoundError("Stock not found")
        if await self.repo.exists(user_id, stock_id):
            raise ConflictError("Stock already in watchlist")
        await self.repo.add(user_id, stock_id)

    async def remove(self, user_id: uuid.UUID, stock_id: uuid.UUID) -> None:
        removed = await self.repo.remove(user_id, stock_id)
        if not removed:
            raise NotFoundError("Stock not in watchlist")

    async def check(self, user_id: uuid.UUID, stock_id: uuid.UUID) -> bool:
        return await self.repo.exists(user_id, stock_id)

    async def list_watchlist(
        self,
        user_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[WatchlistItemEnriched]:
        rows = await self.repo.list_for_user(user_id, cursor=cursor, limit=limit + 1)
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = [
            WatchlistItemEnriched(
                user_id=entry.user_id,
                stock_id=entry.stock_id,
                created_at=entry.created_at,
                stock_symbol=stock.symbol,
                stock_name=stock.name,
                stock_sector=stock.sector,
                stock_current_price=stock.current_price,
            )
            for entry, stock in rows
        ]
        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[WatchlistItemEnriched](items=items, next_cursor=next_cursor, has_more=has_more)
