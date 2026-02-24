"""Public predictor routes (no auth required)."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_predictor_service
from app.schemas.common import PaginatedResponse
from app.schemas.prediction import PredictionResponse
from app.schemas.predictor import PredictorResponse
from app.services.predictor import PredictorService

router = APIRouter(prefix="/predictors", tags=["predictors"])


@router.get("/{slug}", response_model=PredictorResponse)
async def get_predictor(
    slug: str,
    service: PredictorService = Depends(get_predictor_service),
) -> PredictorResponse:
    return await service.get_by_slug(slug)


@router.get("/{slug}/predictions", response_model=PaginatedResponse[PredictionResponse])
async def get_predictor_predictions(
    slug: str,
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    service: PredictorService = Depends(get_predictor_service),
) -> PaginatedResponse[PredictionResponse]:
    return await service.get_predictions(slug, cursor=cursor, limit=limit)


@router.get("/{slug}/members", response_model=list[PredictorResponse])
async def get_predictor_members(
    slug: str,
    service: PredictorService = Depends(get_predictor_service),
) -> list[PredictorResponse]:
    return await service.list_members(slug)
