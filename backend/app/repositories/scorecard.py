"""PredictorScorecard data access repository."""

import uuid

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.predictor import Predictor
from app.models.scorecard import PredictorScorecard


class ScorecardRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_predictor_id(self, predictor_id: uuid.UUID) -> PredictorScorecard | None:
        return await self.session.get(PredictorScorecard, predictor_id)

    async def upsert(self, data: dict[str, object]) -> PredictorScorecard:
        """Insert or update a scorecard by predictor_id."""
        stmt = (
            pg_insert(PredictorScorecard)
            .values(**data)
            .on_conflict_do_update(
                index_elements=["predictor_id"],
                set_={k: v for k, v in data.items() if k != "predictor_id"},
            )
        )
        await self.session.execute(stmt)
        await self.session.flush()
        scorecard = await self.session.get(PredictorScorecard, data["predictor_id"])
        assert scorecard is not None
        return scorecard

    async def get_leaderboard(
        self,
        *,
        min_predictions: int = 10,
        limit: int = 50,
        offset: int = 0,
    ) -> list[tuple[PredictorScorecard, Predictor]]:
        """Get leaderboard: scorecards joined with predictor info, sorted by accuracy."""
        stmt = (
            select(PredictorScorecard, Predictor)
            .join(Predictor, PredictorScorecard.predictor_id == Predictor.id)
            .where(PredictorScorecard.total_predictions >= min_predictions)
            .order_by(PredictorScorecard.accuracy_pct.desc().nullslast())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.all())
