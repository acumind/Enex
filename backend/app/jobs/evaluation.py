"""Background task for evaluating pending predictions."""

import asyncio
import logging

from app.jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _run_evaluation() -> dict[str, object]:
    from app.core.database import async_session_factory
    from app.services.evaluation import EvaluationService

    async with async_session_factory() as session:
        service = EvaluationService(session)
        evaluated, evaluated_ids = await service.evaluate_pending_predictions()
        await session.commit()

    # Dispatch notification task for evaluated predictions
    if evaluated_ids:
        try:
            from app.jobs.notifications import dispatch_outcome_notifications_task

            dispatch_outcome_notifications_task.delay([str(pid) for pid in evaluated_ids])
        except Exception:
            logger.warning("Failed to dispatch outcome notifications task")

    return {"predictions_evaluated": evaluated}


@celery_app.task(name="evaluate_predictions_task", bind=True, max_retries=1)
def evaluate_predictions_task(self) -> dict[str, int]:  # type: ignore[no-untyped-def]
    """Evaluate all eligible pending predictions."""
    try:
        result = asyncio.run(_run_evaluation())
        logger.info("Evaluation complete: %s", result)
        return result
    except Exception as exc:
        logger.exception("Evaluation task failed")
        raise self.retry(exc=exc, countdown=300) from exc
