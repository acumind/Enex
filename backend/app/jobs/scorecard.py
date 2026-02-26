"""Background task for updating predictor scorecards."""

import asyncio
import logging

from app.jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _run_scorecard_update() -> dict[str, int]:
    from app.core.database import async_session_factory
    from app.services.evaluation import EvaluationService

    async with async_session_factory() as session:
        service = EvaluationService(session)
        updated = await service.update_all_scorecards()
        await session.commit()

    return {"scorecards_updated": updated}


@celery_app.task(name="update_scorecards_task", bind=True, max_retries=1)
def update_scorecards_task(self) -> dict[str, int]:  # type: ignore[no-untyped-def]
    """Recompute all predictor scorecards."""
    from app.jobs.task_tracker import track_task

    track_task(self.request.id, "update_scorecards")
    try:
        result = asyncio.run(_run_scorecard_update())
        logger.info("Scorecard update complete: %s", result)
        return result
    except Exception as exc:
        logger.exception("Scorecard update task failed")
        raise self.retry(exc=exc, countdown=60) from exc
