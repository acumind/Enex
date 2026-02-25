"""Stock business logic: CRUD, CSV seeding."""

import csv
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.stock import Stock
from app.repositories.stock import StockRepository
from app.schemas.common import PaginatedResponse
from app.schemas.stock import StockCreate, StockResponse, StockUpdate


class StockService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = StockRepository(session)

    async def create(self, data: StockCreate) -> StockResponse:
        existing = await self.repo.get_by_symbol(data.symbol)
        if existing is not None:
            raise ConflictError(f"Stock with symbol {data.symbol} already exists")

        stock = Stock(
            symbol=data.symbol,
            name=data.name,
            exchange=data.exchange,
            bse_code=data.bse_code,
            sector=data.sector,
            industry=data.industry,
        )
        stock = await self.repo.create(stock)
        return StockResponse.model_validate(stock)

    async def update(self, stock_id: uuid.UUID, data: StockUpdate) -> StockResponse:
        stock = await self.repo.get_by_id(stock_id)
        if stock is None:
            raise NotFoundError("Stock not found")

        update_data = data.model_dump(exclude_unset=True)
        await self.repo.update(stock, update_data)
        return StockResponse.model_validate(stock)

    async def get_by_symbol(self, symbol: str) -> StockResponse:
        stock = await self.repo.get_by_symbol(symbol.upper())
        if stock is None:
            raise NotFoundError(f"Stock {symbol} not found")
        return StockResponse.model_validate(stock)

    async def list_with_filters(
        self,
        *,
        sector: str | None = None,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[StockResponse]:
        stocks = await self.repo.list_with_filters(sector=sector, cursor=cursor, limit=limit + 1)
        has_more = len(stocks) > limit
        if has_more:
            stocks = stocks[:limit]

        items = [StockResponse.model_validate(s) for s in stocks]
        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[StockResponse](items=items, next_cursor=next_cursor, has_more=has_more)

    async def list_active(
        self,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[StockResponse]:
        stocks = await self.repo.list_active(cursor=cursor, limit=limit + 1)
        has_more = len(stocks) > limit
        if has_more:
            stocks = stocks[:limit]

        items = [StockResponse.model_validate(s) for s in stocks]
        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[StockResponse](items=items, next_cursor=next_cursor, has_more=has_more)

    async def seed_from_csv(self, csv_path: str) -> int:
        """Read CSV and bulk insert stocks. Returns count of newly inserted rows."""
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV file not found: {csv_path}")

        stocks_data: list[dict] = []  # type: ignore[type-arg]
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stocks_data.append(
                    {
                        "id": uuid.uuid4(),
                        "symbol": row["symbol"].strip().upper(),
                        "name": row["name"].strip(),
                        "exchange": row.get("exchange", "NSE").strip(),
                        "sector": row.get("sector", "").strip() or None,
                        "industry": row.get("industry", "").strip() or None,
                    }
                )

        if not stocks_data:
            return 0

        return await self.repo.bulk_create(stocks_data)
