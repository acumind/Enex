"""Watchlist and follow engagement schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class WatchlistAdd(BaseModel):
    stock_id: uuid.UUID


class WatchlistCheckResponse(BaseModel):
    watching: bool


class WatchlistItemEnriched(BaseModel):
    model_config = {"from_attributes": True}

    user_id: uuid.UUID
    stock_id: uuid.UUID
    created_at: datetime
    stock_symbol: str
    stock_name: str
    stock_sector: str | None = None
    stock_current_price: Decimal | None = None


class FollowAdd(BaseModel):
    predictor_id: uuid.UUID


class FollowCheckResponse(BaseModel):
    following: bool


class FollowItemEnriched(BaseModel):
    model_config = {"from_attributes": True}

    user_id: uuid.UUID
    predictor_id: uuid.UUID
    created_at: datetime
    predictor_name: str
    predictor_slug: str
    predictor_type: str
    predictor_is_verified: bool = False
