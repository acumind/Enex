"""Stock data access repository."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.stock import Stock
from app.repositories.base import BaseRepository


class StockRepository(BaseRepository[Stock]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Stock)

    async def get_by_symbol(self, symbol: str) -> Stock | None:
        result = await self.session.execute(select(Stock).where(Stock.symbol == symbol))
        return result.scalar_one_or_none()

    async def bulk_create(self, stocks_data: list[dict[str, object]]) -> int:
        """Insert stocks, skipping duplicates on symbol conflict. Returns rows inserted."""
        if not stocks_data:
            return 0
        stmt = pg_insert(Stock).values(stocks_data).on_conflict_do_nothing(index_elements=["symbol"])
        result = await self.session.execute(stmt)
        await self.session.flush()
        return int(result.rowcount)  # type: ignore[attr-defined]

    async def list_active(
        self,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[Stock]:
        stmt = select(Stock).where(Stock.is_active.is_(True)).order_by(Stock.created_at.desc())
        if cursor is not None:
            stmt = stmt.where(Stock.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
