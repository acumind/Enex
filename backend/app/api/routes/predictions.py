"""Public prediction routes (no auth required)."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_prediction_service
from app.schemas.common import PaginatedResponse
from app.schemas.prediction import PredictionResponse
from app.services.prediction import PredictionService

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/recent", response_model=PaginatedResponse[PredictionResponse])
async def get_recent_predictions(
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    service: PredictionService = Depends(get_prediction_service),
) -> PaginatedResponse[PredictionResponse]:
    return await service.list_recent(cursor=cursor, limit=limit)
