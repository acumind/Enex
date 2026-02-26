from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_runtime_config_service
from app.core.config import Settings, get_settings
from app.core.database import get_db
from app.schemas.health import HealthResponse
from app.schemas.stats import AnnouncementResponse
from app.services.runtime_config import RuntimeConfigService

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(
    response: Response,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> HealthResponse:
    db_status = "ok"
    redis_status = "ok"

    # Check PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    # Check Redis
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.REDIS_URL)  # type: ignore[no-untyped-call]
        await r.ping()
        await r.aclose()
    except Exception:
        redis_status = "error"

    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"

    if overall == "degraded":
        response.status_code = 503

    return HealthResponse(
        status=overall,
        db=db_status,
        redis=redis_status,
        version=settings.APP_VERSION,
    )


@router.get("/announcement", response_model=AnnouncementResponse)
async def get_announcement(
    config_service: RuntimeConfigService = Depends(get_runtime_config_service),
) -> AnnouncementResponse:
    text_val = await config_service.get("announcement_text", default="") or ""
    type_val = await config_service.get("announcement_type", default="info") or "info"
    return AnnouncementResponse(text=text_val, type=type_val)
