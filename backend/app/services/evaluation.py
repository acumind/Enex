"""Evaluation service — core prediction outcome computation and scorecard generation."""

import logging
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.prediction import Prediction, PredictionOutcome
from app.models.stock import Stock
from app.repositories.outcome import OutcomeRepository
from app.repositories.scorecard import ScorecardRepository
from app.repositories.stock_daily_price import StockDailyPriceRepository
from app.schemas.outcome import EvaluationTriggerResponse

logger = logging.getLogger(__name__)


class EvaluationService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.outcome_repo = OutcomeRepository(session)
        self.price_repo = StockDailyPriceRepository(session)
        self.scorecard_repo = ScorecardRepository(session)
        self.tolerance = Decimal(str(get_settings().OUTCOME_TOLERANCE_PCT / 100))

    async def evaluate_pending_predictions(self, as_of_date: date | None = None) -> tuple[int, list[uuid.UUID]]:
        """Evaluate all eligible predictions. Returns (count evaluated, list of prediction IDs)."""
        if as_of_date is None:
            as_of_date = date.today()

        predictions = await self.outcome_repo.find_ready_for_evaluation(as_of_date)
        evaluated = 0
        evaluated_ids: list[uuid.UUID] = []

        for prediction in predictions:
            outcome = await self._evaluate_single(prediction, as_of_date)
            if outcome is not None:
                await self.outcome_repo.create(outcome)
                evaluated += 1
                evaluated_ids.append(prediction.id)

        return evaluated, evaluated_ids

    async def _evaluate_single(self, prediction: Prediction, eval_date: date) -> PredictionOutcome | None:
        """Evaluate a single prediction against actual prices."""
        # Get actual price on eval date (nearest trading day)
        price_row = await self.price_repo.get_price_on_date(prediction.stock_id, eval_date)
        if price_row is None:
            logger.warning(
                "No price data for stock %s on/before %s, skipping prediction %s",
                prediction.stock_id,
                eval_date,
                prediction.id,
            )
            return None

        actual_price = price_row.adjusted_close or price_row.close_price

        # Get high/low in window from prediction date to eval date
        highest, lowest = await self.price_repo.get_high_low_in_range(
            prediction.stock_id, prediction.prediction_date, eval_date
        )

        target = prediction.target_price
        entry = prediction.price_at_prediction

        # Determine direction: bullish if target > entry, bearish otherwise
        is_bullish = target > entry

        if is_bullish:
            outcome_status = self._evaluate_bullish(target, highest)
        else:
            outcome_status = self._evaluate_bearish(target, lowest)

        # Deviation: how far actual ended up from target
        deviation_pct = (actual_price - target) / target * 100 if target != 0 else Decimal("0")

        now = datetime.now(UTC).replace(tzinfo=None)
        return PredictionOutcome(
            prediction_id=prediction.id,
            outcome_status=outcome_status,
            actual_price=actual_price,
            highest_price=highest,
            lowest_price=lowest,
            deviation_pct=round(deviation_pct, 2),
            evaluated_at=now,
            evaluation_date=eval_date,
        )

    def _evaluate_bullish(self, target: Decimal, highest: Decimal | None) -> str:
        """Bullish: target > entry. Hit if highest >= target."""
        if highest is None:
            return "miss"
        if highest >= target:
            return "hit"
        threshold = target * (1 - self.tolerance)
        if highest >= threshold:
            return "partial_hit"
        return "miss"

    def _evaluate_bearish(self, target: Decimal, lowest: Decimal | None) -> str:
        """Bearish: target < entry. Hit if lowest <= target."""
        if lowest is None:
            return "miss"
        if lowest <= target:
            return "hit"
        threshold = target * (1 + self.tolerance)
        if lowest <= threshold:
            return "partial_hit"
        return "miss"

    async def update_all_scorecards(self) -> int:
        """Recompute scorecards for all predictors with approved predictions. Returns count updated."""
        # Get all predictor IDs with at least one approved prediction
        stmt = select(Prediction.predictor_id).where(Prediction.status == "approved").distinct()
        result = await self.session.execute(stmt)
        predictor_ids = [row[0] for row in result.all()]

        updated = 0
        for predictor_id in predictor_ids:
            data = await self._compute_scorecard(predictor_id)
            if data is not None:
                await self.scorecard_repo.upsert(data)
                updated += 1

        return updated

    async def _compute_scorecard(self, predictor_id: object) -> dict[str, object] | None:
        """Compute scorecard data for a single predictor."""
        counts = await self.outcome_repo.count_by_status_for_predictor(predictor_id)
        hits = counts.get("hit", 0)
        misses = counts.get("miss", 0)
        partial_hits = counts.get("partial_hit", 0)
        total_evaluated = hits + misses + partial_hits

        # Count pending (approved predictions without outcomes)
        pending_stmt = (
            select(func.count())
            .select_from(Prediction)
            .outerjoin(PredictionOutcome, PredictionOutcome.prediction_id == Prediction.id)
            .where(
                Prediction.predictor_id == predictor_id,
                Prediction.status == "approved",
                PredictionOutcome.id.is_(None),
            )
        )
        pending_result = await self.session.execute(pending_stmt)
        pending = pending_result.scalar_one()

        total = total_evaluated + pending

        # Accuracy: (hits + partial_hits * 0.5) / total_evaluated * 100
        accuracy_pct = None
        if total_evaluated > 0:
            accuracy_pct = round(
                (Decimal(hits) + Decimal(partial_hits) * Decimal("0.5")) / Decimal(total_evaluated) * 100,
                2,
            )

        # Average deviation
        avg_dev_stmt = (
            select(func.avg(PredictionOutcome.deviation_pct))
            .join(Prediction, PredictionOutcome.prediction_id == Prediction.id)
            .where(
                Prediction.predictor_id == predictor_id,
                PredictionOutcome.deviation_pct.isnot(None),
            )
        )
        avg_dev_result = await self.session.execute(avg_dev_stmt)
        avg_deviation = avg_dev_result.scalar_one()
        if avg_deviation is not None:
            avg_deviation = round(Decimal(str(avg_deviation)), 2)

        # Average upside predicted
        avg_upside_stmt = select(
            func.avg((Prediction.target_price - Prediction.price_at_prediction) / Prediction.price_at_prediction * 100)
        ).where(
            Prediction.predictor_id == predictor_id,
            Prediction.status == "approved",
            Prediction.price_at_prediction > 0,
        )
        avg_upside_result = await self.session.execute(avg_upside_stmt)
        avg_upside = avg_upside_result.scalar_one()
        if avg_upside is not None:
            avg_upside = round(Decimal(str(avg_upside)), 2)

        # Sector accuracy
        sector_accuracy = await self._compute_sector_accuracy(predictor_id)
        best_sector = None
        worst_sector = None
        if sector_accuracy:
            best_sector = max(sector_accuracy, key=sector_accuracy.get)
            worst_sector = min(sector_accuracy, key=sector_accuracy.get)

        # Streak
        streak = await self._compute_streak(predictor_id)

        # Last prediction date
        last_pred_stmt = select(func.max(Prediction.prediction_date)).where(
            Prediction.predictor_id == predictor_id,
            Prediction.status == "approved",
        )
        last_pred_result = await self.session.execute(last_pred_stmt)
        last_prediction_date = last_pred_result.scalar_one()

        now = datetime.now(UTC).replace(tzinfo=None)
        return {
            "predictor_id": predictor_id,
            "total_predictions": total,
            "hits": hits,
            "misses": misses,
            "partial_hits": partial_hits,
            "pending": pending,
            "accuracy_pct": accuracy_pct,
            "avg_deviation_pct": avg_deviation,
            "avg_upside_predicted": avg_upside,
            "best_sector": best_sector,
            "worst_sector": worst_sector,
            "sector_accuracy": sector_accuracy,
            "streak_current": streak,
            "last_prediction_date": last_prediction_date,
            "last_updated": now,
        }

    async def _compute_sector_accuracy(self, predictor_id: object) -> dict[str, float]:
        """Compute hit rate per sector."""
        stmt = (
            select(
                Stock.sector,
                PredictionOutcome.outcome_status,
                func.count().label("cnt"),
            )
            .join(Prediction, PredictionOutcome.prediction_id == Prediction.id)
            .join(Stock, Prediction.stock_id == Stock.id)
            .where(
                Prediction.predictor_id == predictor_id,
                Stock.sector.isnot(None),
                PredictionOutcome.outcome_status.in_(["hit", "miss", "partial_hit"]),
            )
            .group_by(Stock.sector, PredictionOutcome.outcome_status)
        )
        result = await self.session.execute(stmt)
        rows = result.all()

        # Aggregate per sector
        sector_data: dict[str, dict[str, int]] = {}
        for row in rows:
            sector = row.sector
            if sector not in sector_data:
                sector_data[sector] = {"hit": 0, "miss": 0, "partial_hit": 0}
            sector_data[sector][row.outcome_status] = row.cnt

        sector_accuracy: dict[str, float] = {}
        for sector, counts in sector_data.items():
            total = counts["hit"] + counts["miss"] + counts["partial_hit"]
            if total > 0:
                acc = (counts["hit"] + counts["partial_hit"] * 0.5) / total * 100
                sector_accuracy[sector] = round(acc, 2)

        return sector_accuracy

    async def _compute_streak(self, predictor_id: object) -> int:
        """Compute current streak. Positive = consecutive hits, negative = consecutive misses."""
        stmt = (
            select(PredictionOutcome.outcome_status)
            .join(Prediction, PredictionOutcome.prediction_id == Prediction.id)
            .where(
                Prediction.predictor_id == predictor_id,
                PredictionOutcome.outcome_status.in_(["hit", "miss", "partial_hit"]),
            )
            .order_by(PredictionOutcome.evaluated_at.desc())
        )
        result = await self.session.execute(stmt)
        statuses = [row[0] for row in result.all()]

        if not statuses:
            return 0

        first = statuses[0]
        streak = 0
        if first == "hit":
            for s in statuses:
                if s == "hit":
                    streak += 1
                else:
                    break
        elif first == "miss":
            for s in statuses:
                if s == "miss":
                    streak -= 1
                else:
                    break
        # partial_hit doesn't extend streaks either way
        return streak

    async def run_full_evaluation(self) -> EvaluationTriggerResponse:
        """Run full evaluation pipeline: evaluate predictions + update scorecards."""
        evaluated, evaluated_ids = await self.evaluate_pending_predictions()
        scorecards = await self.update_all_scorecards()
        return EvaluationTriggerResponse(
            message="Evaluation complete",
            predictions_evaluated=evaluated,
            scorecards_updated=scorecards,
            evaluated_prediction_ids=[str(pid) for pid in evaluated_ids],
        )
