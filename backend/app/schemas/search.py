"""Search response schemas."""

import uuid

from pydantic import BaseModel


class SearchHit(BaseModel):
    id: uuid.UUID
    name: str
    slug_or_symbol: str
    type: str  # "predictor" or "stock"
    sub_type: str | None = None  # predictor_type or sector


class SearchResponse(BaseModel):
    predictors: list[SearchHit]
    stocks: list[SearchHit]
