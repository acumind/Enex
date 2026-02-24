"""Public and authenticated prediction routes."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_prediction_service, get_suggestion_service
from app.core.auth import get_current_user
from app.core.database import get_db
from app.core.rate_limit import prediction_submit_limiter
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.prediction import PredictionCreate, PredictionResponse
from app.schemas.suggestion import SuggestionCreate, SuggestionResponse
from app.services.prediction import PredictionService
from app.services.suggestion import SuggestionService

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/recent", response_model=PaginatedResponse[PredictionResponse])
async def get_recent_predictions(
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    service: PredictionService = Depends(get_prediction_service),
) -> PaginatedResponse[PredictionResponse]:
    return await service.list_recent(cursor=cursor, limit=limit)


@router.post("", response_model=PredictionResponse, status_code=201)
async def submit_prediction(
    data: PredictionCreate,
    _rate_limit: None = Depends(prediction_submit_limiter.dependency()),
    user: User = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    result = await service.create(data, submitted_by=user.id)
    await db.commit()
    return result


@router.get("/mine", response_model=PaginatedResponse[PredictionResponse])
async def list_my_predictions(
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
) -> PaginatedResponse[PredictionResponse]:
    return await service.list_by_user(user.id, cursor=cursor, limit=limit)


@router.post("/suggest", response_model=SuggestionResponse, status_code=201)
async def suggest_prediction(
    data: SuggestionCreate,
    user: User = Depends(get_current_user),
    service: SuggestionService = Depends(get_suggestion_service),
    db: AsyncSession = Depends(get_db),
) -> SuggestionResponse:
    result = await service.create(data, submitted_by=user.id)
    await db.commit()
    return result
