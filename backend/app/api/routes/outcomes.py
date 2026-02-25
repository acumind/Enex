"""Public outcome, leaderboard, and scorecard routes."""

import hashlib
import json
import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_evaluation_service
from app.core.cache import cache_get, cache_set
from app.core.exceptions import NotFoundError
from app.core.rate_limit import public_ip_limiter
from app.repositories.outcome import OutcomeRepository
from app.repositories.scorecard import ScorecardRepository
from app.schemas.outcome import LeaderboardEntry, PredictionOutcomeResponse, ScorecardResponse
from app.services.evaluation import EvaluationService

router = APIRouter(tags=["outcomes"])


@router.get("/outcomes/{prediction_id}", response_model=PredictionOutcomeResponse)
async def get_outcome(
    prediction_id: uuid.UUID,
    _rate_limit: None = Depends(public_ip_limiter.ip_dependency()),
    service: EvaluationService = Depends(get_evaluation_service),
) -> PredictionOutcomeResponse:
    outcome_repo = OutcomeRepository(service.session)
    outcome = await outcome_repo.get_by_prediction_id(prediction_id)
    if outcome is None:
        raise NotFoundError("Outcome not found for this prediction")
    return PredictionOutcomeResponse.model_validate(outcome)


@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    min_predictions: int = Query(10, ge=1),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    predictor_type: str | None = Query(None),
    sort_by: str = Query("accuracy"),
    _rate_limit: None = Depends(public_ip_limiter.ip_dependency()),
    service: EvaluationService = Depends(get_evaluation_service),
) -> list[LeaderboardEntry]:
    # Check cache
    key_parts = f"{min_predictions}:{limit}:{offset}:{predictor_type}:{sort_by}"
    cache_key = f"cache:leaderboard:{hashlib.md5(key_parts.encode()).hexdigest()}"  # noqa: S324
    cached = await cache_get(cache_key)
    if cached is not None:
        return [LeaderboardEntry.model_validate(item) for item in json.loads(cached)]

    scorecard_repo = ScorecardRepository(service.session)
    rows = await scorecard_repo.get_leaderboard(
        min_predictions=min_predictions,
        limit=limit,
        offset=offset,
        predictor_type=predictor_type,
        sort_by=sort_by,
    )
    entries = [
        LeaderboardEntry(
            predictor_id=scorecard.predictor_id,
            predictor_name=predictor.name,
            predictor_slug=predictor.slug,
            predictor_type=predictor.type,
            total_predictions=scorecard.total_predictions,
            hits=scorecard.hits,
            misses=scorecard.misses,
            partial_hits=scorecard.partial_hits,
            accuracy_pct=scorecard.accuracy_pct,
            avg_deviation_pct=scorecard.avg_deviation_pct,
            streak_current=scorecard.streak_current,
        )
        for scorecard, predictor in rows
    ]
    await cache_set(cache_key, json.dumps([e.model_dump(mode="json") for e in entries]), 120)
    return entries


@router.get("/scorecards/{predictor_id}", response_model=ScorecardResponse)
async def get_scorecard(
    predictor_id: uuid.UUID,
    _rate_limit: None = Depends(public_ip_limiter.ip_dependency()),
    service: EvaluationService = Depends(get_evaluation_service),
) -> ScorecardResponse:
    scorecard_repo = ScorecardRepository(service.session)
    scorecard = await scorecard_repo.get_by_predictor_id(predictor_id)
    if scorecard is None:
        raise NotFoundError("Scorecard not found for this predictor")
    return ScorecardResponse.model_validate(scorecard)
