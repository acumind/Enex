"""Stock request/response schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class StockCreate(BaseModel):
    symbol: str = Field(..., pattern=r"^[A-Z0-9&\-]+$", max_length=30)
    name: str = Field(..., min_length=1, max_length=200)
    exchange: str = Field(default="NSE", max_length=10)
    bse_code: str | None = Field(None, max_length=10)
    sector: str | None = Field(None, max_length=100)
    industry: str | None = Field(None, max_length=100)


class StockUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    bse_code: str | None = Field(None, max_length=10)
    sector: str | None = Field(None, max_length=100)
    industry: str | None = Field(None, max_length=100)
    is_active: bool | None = None


class StockResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    symbol: str
    name: str
    exchange: str
    bse_code: str | None
    sector: str | None
    industry: str | None
    market_cap: int | None
    current_price: Decimal | None
    price_updated_at: datetime | None
    is_active: bool
    created_at: datetime
