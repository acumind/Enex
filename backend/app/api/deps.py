"""Dependency injection providers for service classes."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.audit_log import AuditLogService
from app.services.auth import AuthService
from app.services.evaluation import EvaluationService
from app.services.extraction import ExtractionService
from app.services.follow import FollowService
from app.services.notification import NotificationService
from app.services.prediction import PredictionService
from app.services.predictor import PredictorService
from app.services.price_fetcher import PriceFetcherService
from app.services.runtime_config import RuntimeConfigService
from app.services.stats import StatsService
from app.services.stock import StockService
from app.services.suggestion import SuggestionService
from app.services.user import UserService
from app.services.watchlist import WatchlistService


def get_stats_service(db: AsyncSession = Depends(get_db)) -> StatsService:
    return StatsService(db)


def get_audit_log_service(db: AsyncSession = Depends(get_db)) -> AuditLogService:
    return AuditLogService(db)


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)


def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)


def get_predictor_service(db: AsyncSession = Depends(get_db)) -> PredictorService:
    return PredictorService(db)


def get_stock_service(db: AsyncSession = Depends(get_db)) -> StockService:
    return StockService(db)


def get_prediction_service(db: AsyncSession = Depends(get_db)) -> PredictionService:
    return PredictionService(db)


def get_extraction_service() -> ExtractionService:
    return ExtractionService()


def get_suggestion_service(db: AsyncSession = Depends(get_db)) -> SuggestionService:
    return SuggestionService(db)


def get_evaluation_service(db: AsyncSession = Depends(get_db)) -> EvaluationService:
    return EvaluationService(db)


def get_price_fetcher_service(db: AsyncSession = Depends(get_db)) -> PriceFetcherService:
    return PriceFetcherService(db)


def get_watchlist_service(db: AsyncSession = Depends(get_db)) -> WatchlistService:
    return WatchlistService(db)


def get_follow_service(db: AsyncSession = Depends(get_db)) -> FollowService:
    return FollowService(db)


def get_notification_service(db: AsyncSession = Depends(get_db)) -> NotificationService:
    return NotificationService(db)


def get_runtime_config_service(db: AsyncSession = Depends(get_db)) -> RuntimeConfigService:
    return RuntimeConfigService(db)
