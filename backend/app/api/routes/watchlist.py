"""Watchlist routes (authenticated)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.api.deps import get_watchlist_service
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.engagement import WatchlistAdd, WatchlistCheckResponse, WatchlistItemEnriched
from app.services.watchlist import WatchlistService

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.post("", status_code=201)
async def add_to_watchlist(
    data: WatchlistAdd,
    user: User = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await service.add(user.id, data.stock_id)
    await db.commit()
    return {"message": "Added to watchlist"}


@router.delete("/{stock_id}", status_code=204)
async def remove_from_watchlist(
    stock_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await service.remove(user.id, stock_id)
    await db.commit()
    return Response(status_code=204)


@router.get("", response_model=PaginatedResponse[WatchlistItemEnriched])
async def list_watchlist(
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> PaginatedResponse[WatchlistItemEnriched]:
    return await service.list_watchlist(user.id, cursor=cursor, limit=limit)


@router.get("/check/{stock_id}", response_model=WatchlistCheckResponse)
async def check_watchlist(
    stock_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: WatchlistService = Depends(get_watchlist_service),
) -> WatchlistCheckResponse:
    watching = await service.check(user.id, stock_id)
    return WatchlistCheckResponse(watching=watching)
