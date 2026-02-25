"""Follow predictor routes (authenticated)."""

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.api.deps import get_follow_service
from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.engagement import FollowAdd, FollowCheckResponse, FollowItemEnriched
from app.services.follow import FollowService

router = APIRouter(prefix="/following", tags=["following"])


@router.post("", status_code=201)
async def follow_predictor(
    data: FollowAdd,
    user: User = Depends(get_current_user),
    service: FollowService = Depends(get_follow_service),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await service.add(user.id, data.predictor_id)
    await db.commit()
    return {"message": "Now following predictor"}


@router.delete("/{predictor_id}", status_code=204)
async def unfollow_predictor(
    predictor_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: FollowService = Depends(get_follow_service),
    db: AsyncSession = Depends(get_db),
) -> Response:
    await service.remove(user.id, predictor_id)
    await db.commit()
    return Response(status_code=204)


@router.get("", response_model=PaginatedResponse[FollowItemEnriched])
async def list_following(
    cursor: datetime | None = Query(None),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    service: FollowService = Depends(get_follow_service),
) -> PaginatedResponse[FollowItemEnriched]:
    return await service.list_following(user.id, cursor=cursor, limit=limit)


@router.get("/check/{predictor_id}", response_model=FollowCheckResponse)
async def check_following(
    predictor_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: FollowService = Depends(get_follow_service),
) -> FollowCheckResponse:
    following = await service.check(user.id, predictor_id)
    return FollowCheckResponse(following=following)
