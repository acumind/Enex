"""Platform statistics aggregation service."""

import logging
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cached_response
from app.models.prediction import Prediction, PredictionOutcome, PredictionSuggestion
from app.models.predictor import Predictor
from app.models.scorecard import PredictorScorecard
from app.models.stock import Stock
from app.models.user import User
from app.schemas.stats import (
    AdminAlert,
    AdminAlertsResponse,
    AdminStatsResponse,
    EvalDashboardResponse,
    PlatformStatsResponse,
    RecentEvaluation,
    SystemHealthResponse,
)

logger = logging.getLogger(__name__)


class StatsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_admin_stats(self) -> AdminStatsResponse:
        pending_predictions = (
            await self.session.scalar(
                select(func.count()).select_from(Prediction).where(Prediction.status == "pending_review")
            )
            or 0
        )
        pending_suggestions = (
            await self.session.scalar(
                select(func.count()).select_from(PredictionSuggestion).where(PredictionSuggestion.status == "pending")
            )
            or 0
        )
        total_users = await self.session.scalar(select(func.count()).select_from(User)) or 0
        total_predictors = await self.session.scalar(select(func.count()).select_from(Predictor)) or 0
        total_stocks = await self.session.scalar(select(func.count()).select_from(Stock)) or 0

        now = datetime.now(UTC).replace(tzinfo=None)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())

        predictions_today = (
            await self.session.scalar(
                select(func.count()).select_from(Prediction).where(Prediction.created_at >= today_start)
            )
            or 0
        )
        predictions_this_week = (
            await self.session.scalar(
                select(func.count()).select_from(Prediction).where(Prediction.created_at >= week_start)
            )
            or 0
        )

        return AdminStatsResponse(
            pending_predictions=pending_predictions,
            pending_suggestions=pending_suggestions,
            total_users=total_users,
            total_predictors=total_predictors,
            total_stocks=total_stocks,
            predictions_today=predictions_today,
            predictions_this_week=predictions_this_week,
        )

    @cached_response("platform_stats", ttl_seconds=300)
    async def get_platform_stats(self) -> PlatformStatsResponse:
        # Total approved predictions
        total_predictions = (
            await self.session.scalar(
                select(func.count()).select_from(Prediction).where(Prediction.status == "approved")
            )
            or 0
        )

        # Distinct predictors with ≥1 approved prediction
        total_predictors = (
            await self.session.scalar(
                select(func.count(func.distinct(Prediction.predictor_id))).where(Prediction.status == "approved")
            )
            or 0
        )

        # Distinct stocks with ≥1 approved prediction
        total_stocks = (
            await self.session.scalar(
                select(func.count(func.distinct(Prediction.stock_id))).where(Prediction.status == "approved")
            )
            or 0
        )

        # Average accuracy from scorecards with ≥10 predictions
        avg_accuracy_pct = await self.session.scalar(
            select(func.avg(PredictorScorecard.accuracy_pct)).where(PredictorScorecard.total_predictions >= 10)
        )

        # Total evaluated outcomes
        total_evaluated = await self.session.scalar(select(func.count()).select_from(PredictionOutcome)) or 0

        return PlatformStatsResponse(
            total_predictions=total_predictions,
            total_predictors=total_predictors,
            total_stocks=total_stocks,
            avg_accuracy_pct=avg_accuracy_pct,
            total_evaluated=total_evaluated,
        )

    async def get_system_health(self) -> SystemHealthResponse:
        from app.core.database import engine

        # DB pool stats
        pool = engine.pool
        pool_size = pool.size()
        pool_checked_in = pool.checkedin()
        pool_checked_out = pool.checkedout()
        pool_overflow = pool.overflow()

        # Redis health
        redis_latency_ms = None
        redis_memory = None
        redis_connected_clients = None
        try:
            import redis.asyncio as aioredis

            from app.core.config import get_settings

            r = aioredis.from_url(get_settings().REDIS_URL, decode_responses=True)
            try:
                start = time.monotonic()
                await r.ping()
                redis_latency_ms = round((time.monotonic() - start) * 1000, 2)

                info = await r.info("memory")
                redis_memory = info.get("used_memory_human", "unknown")

                clients_info = await r.info("clients")
                redis_connected_clients = clients_info.get("connected_clients", 0)
            finally:
                await r.aclose()
        except Exception:
            logger.warning("Failed to check Redis health")

        # Celery health
        celery_workers = 0
        celery_active_tasks = 0
        celery_reserved_tasks = 0
        try:
            from app.jobs.celery_app import celery_app

            inspect = celery_app.control.inspect(timeout=2.0)

            ping_result = inspect.ping()
            if ping_result:
                celery_workers = len(ping_result)

            active = inspect.active()
            if active:
                celery_active_tasks = sum(len(tasks) for tasks in active.values())

            reserved = inspect.reserved()
            if reserved:
                celery_reserved_tasks = sum(len(tasks) for tasks in reserved.values())
        except Exception:
            logger.warning("Failed to check Celery health")

        return SystemHealthResponse(
            db_pool_size=pool_size,
            db_pool_checked_in=pool_checked_in,
            db_pool_checked_out=pool_checked_out,
            db_pool_overflow=pool_overflow,
            redis_latency_ms=redis_latency_ms,
            redis_memory=redis_memory,
            redis_connected_clients=redis_connected_clients,
            celery_workers=celery_workers,
            celery_active_tasks=celery_active_tasks,
            celery_reserved_tasks=celery_reserved_tasks,
        )

    async def get_eval_dashboard(self) -> EvalDashboardResponse:
        # Count outcomes by status
        status_counts = await self.session.execute(
            select(PredictionOutcome.outcome_status, func.count()).group_by(PredictionOutcome.outcome_status)
        )
        counts: dict[str, int] = {}
        total_evaluated = 0
        for status, count in status_counts:
            counts[status] = count
            total_evaluated += count

        hits = counts.get("hit", 0)
        misses = counts.get("miss", 0)
        partial_hits = counts.get("partial_hit", 0)

        # Count pending (approved predictions without outcomes)
        total_pending = (
            await self.session.scalar(
                select(func.count())
                .select_from(Prediction)
                .outerjoin(PredictionOutcome, Prediction.id == PredictionOutcome.prediction_id)
                .where(and_(Prediction.status == "approved", PredictionOutcome.id.is_(None)))
            )
            or 0
        )

        # Accuracy
        scorable = hits + misses + partial_hits
        accuracy_pct = round((hits + partial_hits * 0.5) / scorable * 100, 2) if scorable > 0 else None

        # Avg deviation
        avg_deviation = await self.session.scalar(
            select(func.avg(PredictionOutcome.deviation_pct)).where(PredictionOutcome.deviation_pct.is_not(None))
        )
        avg_deviation_pct = round(float(avg_deviation), 2) if avg_deviation is not None else None

        # Recent evaluations (last 10)
        recent_stmt = (
            select(
                PredictionOutcome.prediction_id,
                Stock.symbol,
                Predictor.name,
                PredictionOutcome.outcome_status,
                PredictionOutcome.deviation_pct,
                PredictionOutcome.evaluated_at,
            )
            .join(Prediction, PredictionOutcome.prediction_id == Prediction.id)
            .join(Stock, Prediction.stock_id == Stock.id)
            .join(Predictor, Prediction.predictor_id == Predictor.id)
            .where(PredictionOutcome.evaluated_at.is_not(None))
            .order_by(PredictionOutcome.evaluated_at.desc())
            .limit(10)
        )
        recent_result = await self.session.execute(recent_stmt)
        recent_evaluations = [
            RecentEvaluation(
                prediction_id=str(row.prediction_id),
                stock_symbol=row.symbol,
                predictor_name=row.name,
                outcome_status=row.outcome_status,
                deviation_pct=float(row.deviation_pct) if row.deviation_pct is not None else None,
                evaluated_at=row.evaluated_at.isoformat() if row.evaluated_at else "",
            )
            for row in recent_result
        ]

        # Today / this week counts
        now = datetime.now(UTC).replace(tzinfo=None)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=today_start.weekday())

        evaluations_today = (
            await self.session.scalar(
                select(func.count()).select_from(PredictionOutcome).where(PredictionOutcome.evaluated_at >= today_start)
            )
            or 0
        )
        evaluations_this_week = (
            await self.session.scalar(
                select(func.count()).select_from(PredictionOutcome).where(PredictionOutcome.evaluated_at >= week_start)
            )
            or 0
        )

        return EvalDashboardResponse(
            total_evaluated=total_evaluated,
            total_pending=total_pending,
            hits=hits,
            misses=misses,
            partial_hits=partial_hits,
            accuracy_pct=accuracy_pct,
            avg_deviation_pct=avg_deviation_pct,
            recent_evaluations=recent_evaluations,
            evaluations_today=evaluations_today,
            evaluations_this_week=evaluations_this_week,
        )

    async def get_admin_alerts(self) -> AdminAlertsResponse:
        alerts: list[AdminAlert] = []

        # Check queue sizes
        admin_stats = await self.get_admin_stats()

        if admin_stats.pending_predictions > 100:
            alerts.append(
                AdminAlert(
                    level="critical",
                    category="queue",
                    message=f"Critical: {admin_stats.pending_predictions} predictions pending review",
                )
            )
        elif admin_stats.pending_predictions > 50:
            alerts.append(
                AdminAlert(
                    level="warning",
                    category="queue",
                    message=f"High pending prediction queue: {admin_stats.pending_predictions}",
                )
            )

        if admin_stats.pending_suggestions > 30:
            alerts.append(
                AdminAlert(
                    level="warning",
                    category="queue",
                    message=f"High pending suggestion queue: {admin_stats.pending_suggestions}",
                )
            )

        # Check system health
        health = await self.get_system_health()

        if health.db_pool_size > 0 and health.db_pool_checked_out > health.db_pool_size * 0.8:
            alerts.append(
                AdminAlert(
                    level="warning",
                    category="health",
                    message=f"DB pool running low: {health.db_pool_checked_out}/{health.db_pool_size} in use",
                )
            )

        if health.celery_workers == 0:
            alerts.append(
                AdminAlert(
                    level="critical",
                    category="health",
                    message="No Celery workers online",
                )
            )

        if health.redis_latency_ms is not None and health.redis_latency_ms > 100:
            alerts.append(
                AdminAlert(
                    level="warning",
                    category="health",
                    message=f"Redis latency elevated: {health.redis_latency_ms}ms",
                )
            )

        return AdminAlertsResponse(
            alerts=alerts,
            checked_at=datetime.now(UTC).isoformat(),
        )
