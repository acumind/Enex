"""Background task for fetching daily stock prices."""

import asyncio
import logging

from app.jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _run_price_fetch() -> dict[str, object]:
    from app.core.database import async_session_factory
    from app.services.price_fetcher import PriceFetcherService

    async with async_session_factory() as session:
        service = PriceFetcherService(session)
        upserted = await service.fetch_all_active_stocks()
        updated = await service.update_current_prices()
        await session.commit()

    return {"prices_upserted": upserted, "current_prices_updated": updated}


@celery_app.task(name="fetch_daily_prices_task", bind=True, max_retries=1)
def fetch_daily_prices_task(self) -> dict[str, object]:  # type: ignore[no-untyped-def]
    """Fetch daily prices for all active stocks."""
    from app.jobs.task_tracker import track_task

    track_task(self.request.id, "fetch_daily_prices")
    try:
        result = asyncio.run(_run_price_fetch())
        logger.info("Price fetch complete: %s", result)
        return result
    except Exception as exc:
        logger.exception("Price fetch task failed")
        raise self.retry(exc=exc, countdown=300) from exc
