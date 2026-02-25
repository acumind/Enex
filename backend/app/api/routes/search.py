"""Public search route across predictors and stocks."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.predictor import PredictorRepository
from app.repositories.stock import StockRepository
from app.schemas.search import SearchHit, SearchResponse

router = APIRouter(tags=["search"])


@router.get("/search", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    predictor_repo = PredictorRepository(db)
    stock_repo = StockRepository(db)

    predictors = await predictor_repo.search(q, limit=limit)
    stocks = await stock_repo.search(q, limit=limit)

    return SearchResponse(
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
