"""Public platform statistics endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.rate_limit import public_ip_limiter
from app.schemas.stats import PlatformStatsResponse
from app.services.stats import StatsService

router = APIRouter(tags=["stats"])


@router.get("/stats", response_model=PlatformStatsResponse)
async def get_platform_stats(
    _rate_limit: None = Depends(public_ip_limiter.ip_dependency()),
    db: AsyncSession = Depends(get_db),
) -> PlatformStatsResponse:
    service = StatsService(db)
    return await service.get_platform_stats()
