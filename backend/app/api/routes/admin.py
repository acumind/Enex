"""Admin and moderator routes (auth required)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_evaluation_service,
    get_prediction_service,
    get_predictor_service,
    get_stock_service,
    get_suggestion_service,
    get_user_service,
)
from app.core.auth import require_role
from app.core.database import get_db
from app.core.rate_limit import bulk_extract_limiter
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.outcome import EvaluationTriggerResponse
from app.schemas.prediction import PredictionCreate, PredictionResponse
from app.schemas.predictor import PredictorCreate, PredictorResponse, PredictorUpdate
from app.schemas.stock import StockCreate, StockResponse
from app.schemas.suggestion import BulkExtractRequest, BulkExtractResponse, SuggestionResponse
from app.schemas.user import RoleChange, UserBan, UserResponse
from app.services.evaluation import EvaluationService
from app.services.prediction import PredictionService
from app.services.predictor import PredictorService
from app.services.stock import StockService
from app.services.suggestion import SuggestionService
from app.services.user import UserService

router = APIRouter(prefix="/admin", tags=["admin"])

# Dependency shortcuts
_admin = require_role("admin")
_moderator_or_admin = require_role("moderator", "admin")


# --- Predictors ---


@router.post("/predictors", response_model=PredictorResponse, status_code=201)
async def create_predictor(
    data: PredictorCreate,
    user: User = Depends(_admin),
    service: PredictorService = Depends(get_predictor_service),
    db: AsyncSession = Depends(get_db),
) -> PredictorResponse:
    result = await service.create(data)
    await db.commit()
    return result


@router.patch("/predictors/{predictor_id}", response_model=PredictorResponse)
async def update_predictor(
    predictor_id: uuid.UUID,
    data: PredictorUpdate,
    user: User = Depends(_admin),
    service: PredictorService = Depends(get_predictor_service),
    db: AsyncSession = Depends(get_db),
) -> PredictorResponse:
    result = await service.update(predictor_id, data)
    await db.commit()
    return result


# --- Stocks ---


@router.post("/stocks", response_model=StockResponse, status_code=201)
async def create_stock(
    data: StockCreate,
    user: User = Depends(_admin),
    service: StockService = Depends(get_stock_service),
    db: AsyncSession = Depends(get_db),
) -> StockResponse:
    result = await service.create(data)
    await db.commit()
    return result


# --- Review Queue ---


@router.get("/review-queue", response_model=PaginatedResponse[PredictionResponse])
async def get_review_queue(
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(_moderator_or_admin),
    service: PredictionService = Depends(get_prediction_service),
) -> PaginatedResponse[PredictionResponse]:
    return await service.list_review_queue(cursor=cursor, limit=limit)


@router.post("/predictions", response_model=PredictionResponse, status_code=201)
async def create_prediction(
    data: PredictionCreate,
    user: User = Depends(_moderator_or_admin),
    service: PredictionService = Depends(get_prediction_service),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    result = await service.create(data, submitted_by=user.id)
    await db.commit()
    return result


@router.post("/predictions/{prediction_id}/approve", response_model=PredictionResponse)
async def approve_prediction(
    prediction_id: uuid.UUID,
    user: User = Depends(_moderator_or_admin),
    service: PredictionService = Depends(get_prediction_service),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    result = await service.approve(prediction_id, reviewer_id=user.id)
    await db.commit()
    return result


@router.post("/predictions/{prediction_id}/reject", response_model=PredictionResponse)
async def reject_prediction(
    prediction_id: uuid.UUID,
    user: User = Depends(_moderator_or_admin),
    service: PredictionService = Depends(get_prediction_service),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    result = await service.reject(prediction_id, reviewer_id=user.id)
    await db.commit()
    return result


# --- Suggestions ---


@router.get("/suggestions", response_model=PaginatedResponse[SuggestionResponse])
async def list_suggestions(
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(_moderator_or_admin),
    service: SuggestionService = Depends(get_suggestion_service),
) -> PaginatedResponse[SuggestionResponse]:
    return await service.list_pending(cursor=cursor, limit=limit)


@router.post("/suggestions/{suggestion_id}/promote", response_model=SuggestionResponse)
async def promote_suggestion(
    suggestion_id: uuid.UUID,
    user: User = Depends(_moderator_or_admin),
    service: SuggestionService = Depends(get_suggestion_service),
    db: AsyncSession = Depends(get_db),
) -> SuggestionResponse:
    result = await service.promote(suggestion_id, reviewer_id=user.id)
    await db.commit()
    return result


@router.post("/suggestions/{suggestion_id}/dismiss", response_model=SuggestionResponse)
async def dismiss_suggestion(
    suggestion_id: uuid.UUID,
    user: User = Depends(_moderator_or_admin),
    service: SuggestionService = Depends(get_suggestion_service),
    db: AsyncSession = Depends(get_db),
) -> SuggestionResponse:
    result = await service.dismiss(suggestion_id, reviewer_id=user.id)
    await db.commit()
    return result


# --- Bulk Extract ---


@router.post("/bulk-extract", response_model=BulkExtractResponse, status_code=202)
async def bulk_extract(
    data: BulkExtractRequest,
    _rate_limit: None = Depends(bulk_extract_limiter.dependency()),
    user: User = Depends(_admin),
) -> BulkExtractResponse:
    from app.jobs.extraction import extract_prediction_task

    job_id = uuid.uuid4().hex
    for url in data.urls:
        extract_prediction_task.delay(None, str(user.id), url)
    return BulkExtractResponse(
        job_id=job_id,
        total=len(data.urls),
        message=f"Queued {len(data.urls)} URLs for extraction",
    )


# --- Users ---


@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_users(
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(_admin),
    service: UserService = Depends(get_user_service),
) -> PaginatedResponse[UserResponse]:
    return await service.list_users(cursor=cursor, limit=limit)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: uuid.UUID,
    data: RoleChange,
    user: User = Depends(_admin),
    service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    result = await service.change_role(user_id, data.role)
    await db.commit()
    return result


@router.patch("/users/{user_id}/ban", response_model=UserResponse)
async def ban_user(
    user_id: uuid.UUID,
    data: UserBan,
    user: User = Depends(_admin),
    service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    result = await service.ban_user(user_id, data.ban_reason)
    await db.commit()
    return result


@router.delete("/users/{user_id}/ban", response_model=UserResponse)
async def unban_user(
    user_id: uuid.UUID,
    user: User = Depends(_admin),
    service: UserService = Depends(get_user_service),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    result = await service.unban_user(user_id)
    await db.commit()
    return result


# --- Evaluation ---


@router.post("/trigger-evaluation", response_model=EvaluationTriggerResponse)
async def trigger_evaluation(
    user: User = Depends(_admin),
    service: EvaluationService = Depends(get_evaluation_service),
    db: AsyncSession = Depends(get_db),
) -> EvaluationTriggerResponse:
    result = await service.run_full_evaluation()
    await db.commit()
    return result
