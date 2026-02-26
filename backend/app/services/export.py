"""CSV streaming generators for admin data export."""

import csv
import io
from collections.abc import AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.prediction import Prediction, PredictionOutcome
from app.models.predictor import Predictor
from app.models.scorecard import PredictorScorecard
from app.models.stock import Stock


def _row_to_csv(row: list[str]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(row)
    return buf.getvalue()


async def stream_predictions_csv(session: AsyncSession) -> AsyncGenerator[str, None]:
    headers = [
        "prediction_id",
        "predictor_name",
        "stock_symbol",
        "stock_name",
        "target_price",
        "price_at_prediction",
        "upside_pct",
        "prediction_date",
        "target_date",
        "default_eval_date",
        "source_url",
        "source_type",
        "extraction_method",
        "status",
        "created_at",
    ]
    yield _row_to_csv(headers)

    stmt = (
        select(
            Prediction.id,
            Predictor.name,
            Stock.symbol,
            Stock.name,
            Prediction.target_price,
            Prediction.price_at_prediction,
            Prediction.upside_pct,
            Prediction.prediction_date,
            Prediction.target_date,
            Prediction.default_eval_date,
            Prediction.source_url,
            Prediction.source_type,
            Prediction.extraction_method,
            Prediction.status,
            Prediction.created_at,
        )
        .join(Stock, Prediction.stock_id == Stock.id)
        .join(Predictor, Prediction.predictor_id == Predictor.id)
        .where(Prediction.status == "approved")
        .order_by(Prediction.prediction_date.desc())
    )
    result = await session.execute(stmt)
    for row in result:
        yield _row_to_csv([str(v) if v is not None else "" for v in row])


async def stream_outcomes_csv(session: AsyncSession) -> AsyncGenerator[str, None]:
    headers = [
        "outcome_id",
        "prediction_id",
        "predictor_name",
        "stock_symbol",
        "target_price",
        "actual_price",
        "deviation_pct",
        "outcome_status",
        "highest_price",
        "lowest_price",
        "evaluated_at",
        "evaluation_date",
    ]
    yield _row_to_csv(headers)

    stmt = (
        select(
            PredictionOutcome.id,
            PredictionOutcome.prediction_id,
            Predictor.name,
            Stock.symbol,
            Prediction.target_price,
            PredictionOutcome.actual_price,
            PredictionOutcome.deviation_pct,
            PredictionOutcome.outcome_status,
            PredictionOutcome.highest_price,
            PredictionOutcome.lowest_price,
            PredictionOutcome.evaluated_at,
            PredictionOutcome.evaluation_date,
        )
        .join(Prediction, PredictionOutcome.prediction_id == Prediction.id)
        .join(Stock, Prediction.stock_id == Stock.id)
        .join(Predictor, Prediction.predictor_id == Predictor.id)
        .order_by(PredictionOutcome.evaluated_at.desc())
    )
    result = await session.execute(stmt)
    for row in result:
        yield _row_to_csv([str(v) if v is not None else "" for v in row])


async def stream_scorecards_csv(session: AsyncSession) -> AsyncGenerator[str, None]:
    headers = [
        "predictor_id",
        "predictor_name",
        "predictor_type",
        "total_predictions",
        "hits",
        "misses",
        "partial_hits",
        "pending",
        "accuracy_pct",
        "avg_deviation_pct",
        "avg_upside_predicted",
        "best_sector",
        "worst_sector",
        "streak_current",
        "last_prediction_date",
        "last_updated",
    ]
    yield _row_to_csv(headers)

    stmt = (
        select(
            PredictorScorecard.predictor_id,
            Predictor.name,
            Predictor.type,
            PredictorScorecard.total_predictions,
            PredictorScorecard.hits,
            PredictorScorecard.misses,
            PredictorScorecard.partial_hits,
            PredictorScorecard.pending,
            PredictorScorecard.accuracy_pct,
            PredictorScorecard.avg_deviation_pct,
            PredictorScorecard.avg_upside_predicted,
            PredictorScorecard.best_sector,
            PredictorScorecard.worst_sector,
            PredictorScorecard.streak_current,
            PredictorScorecard.last_prediction_date,
            PredictorScorecard.last_updated,
        )
        .join(Predictor, PredictorScorecard.predictor_id == Predictor.id)
        .order_by(Predictor.name)
    )
    result = await session.execute(stmt)
    for row in result:
        yield _row_to_csv([str(v) if v is not None else "" for v in row])
