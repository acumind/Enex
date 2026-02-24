"""Public outcome, leaderboard, and scorecard routes."""

import uuid

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_evaluation_service
from app.core.exceptions import NotFoundError
from app.repositories.outcome import OutcomeRepository
from app.repositories.scorecard import ScorecardRepository
from app.schemas.outcome import LeaderboardEntry, PredictionOutcomeResponse, ScorecardResponse
from app.services.evaluation import EvaluationService

router = APIRouter(tags=["outcomes"])


@router.get("/outcomes/{prediction_id}", response_model=PredictionOutcomeResponse)
async def get_outcome(
    prediction_id: uuid.UUID,
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
    service: EvaluationService = Depends(get_evaluation_service),
) -> list[LeaderboardEntry]:
    scorecard_repo = ScorecardRepository(service.session)
    rows = await scorecard_repo.get_leaderboard(min_predictions=min_predictions, limit=limit, offset=offset)
    return [
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


@router.get("/scorecards/{predictor_id}", response_model=ScorecardResponse)
async def get_scorecard(
    predictor_id: uuid.UUID,
    service: EvaluationService = Depends(get_evaluation_service),
) -> ScorecardResponse:
    scorecard_repo = ScorecardRepository(service.session)
    scorecard = await scorecard_repo.get_by_predictor_id(predictor_id)
    if scorecard is None:
        raise NotFoundError("Scorecard not found for this predictor")
    return ScorecardResponse.model_validate(scorecard)
