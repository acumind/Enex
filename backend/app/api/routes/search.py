"""Public search route across predictors and stocks."""

import hashlib

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_get, cache_set
from app.core.database import get_db
from app.core.rate_limit import public_ip_limiter
from app.repositories.predictor import PredictorRepository
from app.repositories.stock import StockRepository
from app.schemas.search import SearchHit, SearchResponse

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    _rate_limit: None = Depends(public_ip_limiter.ip_dependency()),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    # Check cache
    key_parts = f"{q}:{limit}"
    cache_key = f"cache:search:{hashlib.md5(key_parts.encode()).hexdigest()}"  # noqa: S324
    cached = await cache_get(cache_key)
    if cached is not None:
        return SearchResponse.model_validate_json(cached)

    predictor_repo = PredictorRepository(db)
    stock_repo = StockRepository(db)

    predictors = await predictor_repo.search(q, limit=limit)
    stocks = await stock_repo.search(q, limit=limit)

    result = SearchResponse(
        predictors=[
            SearchHit(
                id=p.id,
                name=p.name,
                slug_or_symbol=p.slug,
                type="predictor",
                sub_type=p.type,
            )
            for p in predictors
        ],
        stocks=[
            SearchHit(
                id=s.id,
                name=s.name,
                slug_or_symbol=s.symbol,
                type="stock",
                sub_type=s.sector,
            )
            for s in stocks
        ],
    )
    await cache_set(cache_key, result.model_dump_json(), 60)
    return result
