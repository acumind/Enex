"""Public stock routes (no auth required)."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_prediction_service, get_stock_service
from app.schemas.common import PaginatedResponse
from app.schemas.prediction import PredictionResponse
from app.schemas.stock import StockResponse
from app.services.prediction import PredictionService
from app.services.stock import StockService

router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_model=PaginatedResponse[StockResponse])
async def list_stocks(
    sector: str | None = Query(None),
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    service: StockService = Depends(get_stock_service),
) -> PaginatedResponse[StockResponse]:
    return await service.list_with_filters(sector=sector, cursor=cursor, limit=limit)


@router.get("/{symbol}", response_model=StockResponse)
async def get_stock(
    symbol: str,
    service: StockService = Depends(get_stock_service),
) -> StockResponse:
    return await service.get_by_symbol(symbol)


@router.get("/{symbol}/predictions", response_model=PaginatedResponse[PredictionResponse])
async def get_stock_predictions(
    symbol: str,
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    stock_service: StockService = Depends(get_stock_service),
    prediction_service: PredictionService = Depends(get_prediction_service),
) -> PaginatedResponse[PredictionResponse]:
    # Resolve symbol to stock (raises 404 if not found)
    stock = await stock_service.get_by_symbol(symbol)
    return await prediction_service.list_by_stock(stock.id, cursor=cursor, limit=limit)
