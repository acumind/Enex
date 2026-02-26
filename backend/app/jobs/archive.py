"""Background archival task — saves prediction source URLs to Wayback Machine."""

import asyncio
import logging
import uuid

from app.jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _run_archive(prediction_id: str, url: str) -> None:
    from app.core.database import async_session_factory
    from app.integrations.archive.wayback_adapter import WaybackAdapter
    from app.repositories.prediction import PredictionRepository

    adapter = WaybackAdapter()
    snapshot_url = await adapter.save_url(url)

    if snapshot_url:
        async with async_session_factory() as session:
            repo = PredictionRepository(session)
            prediction = await repo.get_by_id(uuid.UUID(prediction_id))
            if prediction:
                prediction.source_archive_url = snapshot_url
                await session.flush()
                await session.commit()


@celery_app.task(name="archive_url_task", bind=True, max_retries=1)
def archive_url_task(self, prediction_id: str, url: str) -> dict[str, str]:  # type: ignore[no-untyped-def]
    """Archive a URL to the Wayback Machine."""
    from app.jobs.task_tracker import track_task

    track_task(self.request.id, "archive_url")
    try:
        asyncio.run(_run_archive(prediction_id, url))
        return {"status": "ok", "url": url}
    except Exception as exc:
        logger.exception("Archive task failed for %s", url)
        raise self.retry(exc=exc, countdown=60) from exc
