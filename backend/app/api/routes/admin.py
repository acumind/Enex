"""Admin and moderator routes (auth required)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_audit_log_service,
    get_evaluation_service,
    get_notification_service,
    get_prediction_service,
    get_predictor_service,
    get_runtime_config_service,
    get_stats_service,
    get_stock_service,
    get_suggestion_service,
    get_user_service,
)
from app.core.auth import require_role
from app.core.database import get_db
from app.core.rate_limit import bulk_extract_limiter
from app.models.user import User
from app.schemas.audit_log import AuditLogResponse
from app.schemas.common import PaginatedResponse
from app.schemas.notification import BroadcastRequest, BroadcastResponse
from app.schemas.outcome import EvaluationTriggerResponse
from app.schemas.prediction import (
    BulkStatusChangeRequest,
    BulkStatusChangeResponse,
    PredictionCreate,
    PredictionResponse,
    PredictionUpdate,
)
from app.schemas.predictor import PredictorCreate, PredictorResponse, PredictorUpdate
from app.schemas.runtime_config import RuntimeConfigResponse, RuntimeConfigUpdate
from app.schemas.stats import (
    AdminAlertsResponse,
    AdminStatsResponse,
    EvalDashboardResponse,
    JobStatusResponse,
    SystemHealthResponse,
)
from app.schemas.stock import StockCreate, StockResponse, StockUpdate
from app.schemas.suggestion import BulkExtractRequest, BulkExtractResponse, SuggestionResponse
from app.schemas.user import (
    ActiveSessionsResponse,
    LoginEventResponse,
    RoleChange,
    UserBan,
    UserDetailResponse,
    UserResponse,
)
from app.services.audit_log import AuditLogService
from app.services.evaluation import EvaluationService
from app.services.notification import NotificationService
from app.services.prediction import PredictionService
from app.services.predictor import PredictorService
from app.services.runtime_config import RuntimeConfigService
from app.services.stats import StatsService
from app.services.stock import StockService
from app.services.suggestion import SuggestionService
from app.services.user import UserService

router = APIRouter(prefix="/admin", tags=["admin"])

# Dependency shortcuts
_admin = require_role("admin")
_moderator_or_admin = require_role("moderator", "admin")


# --- Stats ---


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    user: User = Depends(_admin),
    service: StatsService = Depends(get_stats_service),
) -> AdminStatsResponse:
    return await service.get_admin_stats()


# --- Predictors ---


@router.post("/predictors", response_model=PredictorResponse, status_code=201)
async def create_predictor(
    data: PredictorCreate,
    user: User = Depends(_admin),
    service: PredictorService = Depends(get_predictor_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> PredictorResponse:
    result = await service.create(data)
    await audit.record(user.id, "predictor.create", "predictor", result.id, {"name": result.name})
    await db.commit()
    return result


@router.get("/predictors", response_model=PaginatedResponse[PredictorResponse])
async def list_predictors(
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    search: str | None = Query(None),
    type: str | None = Query(None),
    user: User = Depends(_admin),
    service: PredictorService = Depends(get_predictor_service),
) -> PaginatedResponse[PredictorResponse]:
    return await service.list_all(search=search, type_filter=type, cursor=cursor, limit=limit)


@router.patch("/predictors/{predictor_id}", response_model=PredictorResponse)
async def update_predictor(
    predictor_id: uuid.UUID,
    data: PredictorUpdate,
    user: User = Depends(_admin),
    service: PredictorService = Depends(get_predictor_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> PredictorResponse:
    result = await service.update(predictor_id, data)
    changes = {k: str(v) for k, v in data.model_dump(exclude_unset=True).items()}
    await audit.record(user.id, "predictor.update", "predictor", predictor_id, changes)
    await db.commit()
    return result


# --- Stocks ---


@router.get("/stocks", response_model=PaginatedResponse[StockResponse])
async def list_stocks(
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    sector: str | None = Query(None),
    user: User = Depends(_admin),
    service: StockService = Depends(get_stock_service),
) -> PaginatedResponse[StockResponse]:
    return await service.list_with_filters(sector=sector, cursor=cursor, limit=limit)


@router.post("/stocks", response_model=StockResponse, status_code=201)
async def create_stock(
    data: StockCreate,
    user: User = Depends(_admin),
    service: StockService = Depends(get_stock_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> StockResponse:
    result = await service.create(data)
    await audit.record(user.id, "stock.create", "stock", result.id, {"symbol": data.symbol})
    await db.commit()
    return result


@router.patch("/stocks/{stock_id}", response_model=StockResponse)
async def update_stock(
    stock_id: uuid.UUID,
    data: StockUpdate,
    user: User = Depends(_admin),
    service: StockService = Depends(get_stock_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> StockResponse:
    result = await service.update(stock_id, data)
    changes = {k: str(v) for k, v in data.model_dump(exclude_unset=True).items()}
    await audit.record(user.id, "stock.update", "stock", stock_id, changes)
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
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    result = await service.create(data, submitted_by=user.id)
    await audit.record(user.id, "prediction.create", "prediction", result.id)
    await db.commit()
    return result


@router.patch("/predictions/{prediction_id}", response_model=PredictionResponse)
async def edit_prediction(
    prediction_id: uuid.UUID,
    data: PredictionUpdate,
    user: User = Depends(_admin),
    service: PredictionService = Depends(get_prediction_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    result = await service.update(prediction_id, data, editor_id=user.id)
    audit_details = {k: str(v) for k, v in data.model_dump(exclude_unset=True).items()}
    await audit.record(user.id, "prediction.edit", "prediction", prediction_id, audit_details)
    await db.commit()
    return result


@router.post("/predictions/{prediction_id}/approve", response_model=PredictionResponse)
async def approve_prediction(
    prediction_id: uuid.UUID,
    user: User = Depends(_moderator_or_admin),
    service: PredictionService = Depends(get_prediction_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    result = await service.approve(prediction_id, reviewer_id=user.id)
    await audit.record(
        user.id,
        "prediction.approve",
        "prediction",
        prediction_id,
        {"old_status": "pending_review", "new_status": "approved"},
    )
    await db.commit()
    return result


@router.post("/predictions/{prediction_id}/reject", response_model=PredictionResponse)
async def reject_prediction(
    prediction_id: uuid.UUID,
    user: User = Depends(_moderator_or_admin),
    service: PredictionService = Depends(get_prediction_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    result = await service.reject(prediction_id, reviewer_id=user.id)
    await audit.record(
        user.id,
        "prediction.reject",
        "prediction",
        prediction_id,
        {"old_status": "pending_review", "new_status": "rejected"},
    )
    await db.commit()
    return result


# --- Bulk Prediction Actions ---


@router.post("/predictions/bulk-approve", response_model=BulkStatusChangeResponse)
async def bulk_approve_predictions(
    data: BulkStatusChangeRequest,
    user: User = Depends(_moderator_or_admin),
    service: PredictionService = Depends(get_prediction_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> BulkStatusChangeResponse:
    updated, failed, errors = await service.bulk_approve(data.prediction_ids, reviewer_id=user.id)
    await audit.record(
        user.id,
        "prediction.bulk_approve",
        "prediction",
        details={"count": updated, "failed": failed},
    )
    await db.commit()
    return BulkStatusChangeResponse(updated=updated, failed=failed, errors=errors)


@router.post("/predictions/bulk-reject", response_model=BulkStatusChangeResponse)
async def bulk_reject_predictions(
    data: BulkStatusChangeRequest,
    user: User = Depends(_moderator_or_admin),
    service: PredictionService = Depends(get_prediction_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> BulkStatusChangeResponse:
    updated, failed, errors = await service.bulk_reject(data.prediction_ids, reviewer_id=user.id)
    await audit.record(
        user.id,
        "prediction.bulk_reject",
        "prediction",
        details={"count": updated, "failed": failed},
    )
    await db.commit()
    return BulkStatusChangeResponse(updated=updated, failed=failed, errors=errors)


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
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> SuggestionResponse:
    result = await service.promote(suggestion_id, reviewer_id=user.id)
    await audit.record(
        user.id,
        "suggestion.promote",
        "suggestion",
        suggestion_id,
        {"old_status": "pending", "new_status": "promoted"},
    )
    await db.commit()
    return result


@router.post("/suggestions/{suggestion_id}/dismiss", response_model=SuggestionResponse)
async def dismiss_suggestion(
    suggestion_id: uuid.UUID,
    user: User = Depends(_moderator_or_admin),
    service: SuggestionService = Depends(get_suggestion_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> SuggestionResponse:
    result = await service.dismiss(suggestion_id, reviewer_id=user.id)
    await audit.record(
        user.id,
        "suggestion.dismiss",
        "suggestion",
        suggestion_id,
        {"old_status": "pending", "new_status": "dismissed"},
    )
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
    search: str | None = Query(None),
    role: str | None = Query(None),
    is_active: bool | None = Query(None),
    user: User = Depends(_admin),
    service: UserService = Depends(get_user_service),
) -> PaginatedResponse[UserResponse]:
    return await service.list_users(search=search, role=role, is_active=is_active, cursor=cursor, limit=limit)


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: uuid.UUID,
    user: User = Depends(_admin),
    service: UserService = Depends(get_user_service),
) -> UserDetailResponse:
    from app.core.exceptions import NotFoundError
    from app.repositories.user import UserRepository

    repo = UserRepository(service.repo.session)
    target = await repo.get_by_id(user_id)
    if target is None:
        raise NotFoundError("User not found")
    return UserDetailResponse.model_validate(target)


@router.patch("/users/{user_id}/role", response_model=UserResponse)
async def change_user_role(
    user_id: uuid.UUID,
    data: RoleChange,
    user: User = Depends(_admin),
    service: UserService = Depends(get_user_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    result = await service.change_role(user_id, data.role)
    await audit.record(user.id, "user.role_change", "user", user_id, {"new_role": data.role})
    await db.commit()
    return result


@router.patch("/users/{user_id}/ban", response_model=UserResponse)
async def ban_user(
    user_id: uuid.UUID,
    data: UserBan,
    user: User = Depends(_admin),
    service: UserService = Depends(get_user_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    result = await service.ban_user(user_id, data.ban_reason)
    await audit.record(user.id, "user.ban", "user", user_id, {"reason": data.ban_reason})
    await db.commit()
    return result


@router.delete("/users/{user_id}/ban", response_model=UserResponse)
async def unban_user(
    user_id: uuid.UUID,
    user: User = Depends(_admin),
    service: UserService = Depends(get_user_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    result = await service.unban_user(user_id)
    await audit.record(user.id, "user.unban", "user", user_id)
    await db.commit()
    return result


@router.get("/users/{user_id}/sessions", response_model=ActiveSessionsResponse)
async def get_user_sessions(
    user_id: uuid.UUID,
    user: User = Depends(_admin),
    db: AsyncSession = Depends(get_db),
) -> ActiveSessionsResponse:
    import redis.asyncio as aioredis

    from app.core.config import get_settings
    from app.repositories.login_event import LoginEventRepository

    login_repo = LoginEventRepository(db)
    events = await login_repo.list_for_user(user_id, limit=20)

    # Count active refresh tokens from Redis
    settings = get_settings()
    refresh_count = 0
    try:
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        try:
            refresh_count = await r.scard(f"user_refresh_tokens:{user_id}")
        finally:
            await r.aclose()
    except Exception:
        pass

    return ActiveSessionsResponse(
        refresh_token_count=refresh_count,
        login_events=[LoginEventResponse.model_validate(e) for e in events],
    )


@router.post("/users/{user_id}/revoke-sessions", response_model=UserResponse)
async def revoke_user_sessions(
    user_id: uuid.UUID,
    user: User = Depends(_admin),
    service: UserService = Depends(get_user_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    from app.core.exceptions import NotFoundError
    from app.core.security import revoke_all_refresh_tokens

    target = await service.repo.get_by_id(user_id)
    if target is None:
        raise NotFoundError("User not found")
    await revoke_all_refresh_tokens(user_id)
    await audit.record(user.id, "user.revoke_sessions", "user", user_id)
    await db.commit()
    return UserResponse.model_validate(target)


# --- Evaluation ---


@router.post("/trigger-evaluation", response_model=EvaluationTriggerResponse)
async def trigger_evaluation(
    user: User = Depends(_admin),
    service: EvaluationService = Depends(get_evaluation_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> EvaluationTriggerResponse:
    result = await service.run_full_evaluation()
    await audit.record(user.id, "evaluation.trigger", "prediction", details={"result": "triggered"})
    await db.commit()
    return result


# --- Audit Log ---


@router.get("/audit-log", response_model=PaginatedResponse[AuditLogResponse])
async def get_audit_log(
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(_admin),
    service: AuditLogService = Depends(get_audit_log_service),
) -> PaginatedResponse[AuditLogResponse]:
    return await service.list_recent(cursor=cursor, limit=limit)


# --- Job Status ---


@router.get("/jobs/recent", response_model=list[JobStatusResponse])
async def get_recent_jobs(
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(_admin),
) -> list[JobStatusResponse]:
    from app.jobs.task_tracker import get_recent_tasks

    tasks = get_recent_tasks(limit=limit)
    return [JobStatusResponse(**t) for t in tasks]


# --- Runtime Config ---


@router.get("/config", response_model=list[RuntimeConfigResponse])
async def list_config(
    user: User = Depends(_admin),
    service: RuntimeConfigService = Depends(get_runtime_config_service),
) -> list[RuntimeConfigResponse]:
    return await service.list_all()


@router.patch("/config/{key}", response_model=RuntimeConfigResponse)
async def update_config(
    key: str,
    data: RuntimeConfigUpdate,
    user: User = Depends(_admin),
    service: RuntimeConfigService = Depends(get_runtime_config_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> RuntimeConfigResponse:
    result = await service.set(key, data.value, updated_by=user.id)
    await audit.record(user.id, "config.update", "config", details={"key": key, "value": data.value})
    await db.commit()
    return result


# --- System Health ---


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    user: User = Depends(_admin),
    service: StatsService = Depends(get_stats_service),
) -> SystemHealthResponse:
    return await service.get_system_health()


# --- Evaluation Dashboard ---


@router.get("/eval-dashboard", response_model=EvalDashboardResponse)
async def get_eval_dashboard(
    user: User = Depends(_admin),
    service: StatsService = Depends(get_stats_service),
) -> EvalDashboardResponse:
    return await service.get_eval_dashboard()


# --- Admin Alerts ---


@router.get("/alerts", response_model=AdminAlertsResponse)
async def get_admin_alerts(
    user: User = Depends(_admin),
    service: StatsService = Depends(get_stats_service),
) -> AdminAlertsResponse:
    return await service.get_admin_alerts()


# --- Data Export (CSV) ---


@router.get("/export/predictions")
async def export_predictions(
    user: User = Depends(_admin),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date as date_type

    from starlette.responses import StreamingResponse

    from app.services.export import stream_predictions_csv

    await audit.record(user.id, "export.predictions", "export")
    await db.commit()
    filename = f"predictions_{date_type.today().isoformat()}.csv"
    return StreamingResponse(
        stream_predictions_csv(db),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/outcomes")
async def export_outcomes(
    user: User = Depends(_admin),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date as date_type

    from starlette.responses import StreamingResponse

    from app.services.export import stream_outcomes_csv

    await audit.record(user.id, "export.outcomes", "export")
    await db.commit()
    filename = f"outcomes_{date_type.today().isoformat()}.csv"
    return StreamingResponse(
        stream_outcomes_csv(db),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/scorecards")
async def export_scorecards(
    user: User = Depends(_admin),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
):
    from datetime import date as date_type

    from starlette.responses import StreamingResponse

    from app.services.export import stream_scorecards_csv

    await audit.record(user.id, "export.scorecards", "export")
    await db.commit()
    filename = f"scorecards_{date_type.today().isoformat()}.csv"
    return StreamingResponse(
        stream_scorecards_csv(db),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# --- Notification Broadcast ---


@router.post("/notifications/broadcast", response_model=BroadcastResponse)
async def broadcast_notification(
    data: BroadcastRequest,
    user: User = Depends(_admin),
    service: NotificationService = Depends(get_notification_service),
    audit: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
) -> BroadcastResponse:
    recipients = await service.broadcast(
        title=data.title,
        message=data.message,
        type=data.type,
        role_filter=data.role_filter,
        sender_id=user.id,
    )
    await audit.record(
        user.id,
        "notification.broadcast",
        "notification",
        details={"title": data.title, "recipients": recipients, "role_filter": data.role_filter},
    )
    await db.commit()
    return BroadcastResponse(recipients=recipients, message=f"Notification sent to {recipients} recipients")
