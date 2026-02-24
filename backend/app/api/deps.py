"""Dependency injection providers for service classes."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.prediction import PredictionService
from app.services.predictor import PredictorService
from app.services.stock import StockService
from app.services.user import UserService


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


def get_predictor_service(db: AsyncSession = Depends(get_db)) -> PredictorService:
    return PredictorService(db)


def get_stock_service(db: AsyncSession = Depends(get_db)) -> StockService:
    return StockService(db)


def get_prediction_service(db: AsyncSession = Depends(get_db)) -> PredictionService:
    return PredictionService(db)
