"""Admin and moderator routes (auth required)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_prediction_service, get_predictor_service, get_stock_service, get_user_service
from app.core.auth import require_role
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.prediction import PredictionCreate, PredictionResponse
from app.schemas.predictor import PredictorCreate, PredictorResponse, PredictorUpdate
from app.schemas.stock import StockCreate, StockResponse
from app.schemas.user import RoleChange, UserBan, UserResponse
from app.services.prediction import PredictionService
from app.services.predictor import PredictorService
from app.services.stock import StockService
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
