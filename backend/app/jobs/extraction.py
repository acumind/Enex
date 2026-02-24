"""Background extraction task — processes suggestions and bulk imports."""

import asyncio
import logging
import re
import uuid

from app.jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


def _slugify(name: str) -> str:
    """Convert a predictor name to a URL-friendly slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


async def _run_extraction(suggestion_id: str | None, reviewer_id: str, url: str) -> None:
    from app.core.database import async_session_factory
    from app.models.prediction import Prediction
    from app.models.predictor import Predictor
    from app.repositories.prediction import PredictionRepository
    from app.repositories.predictor import PredictorRepository
    from app.repositories.stock import StockRepository
    from app.repositories.suggestion import SuggestionRepository
    from app.services.extraction import ExtractionService

    extraction_service = ExtractionService()
    result = await extraction_service.extract_from_url(url)

    async with async_session_factory() as session:
        pred_repo = PredictionRepository(session)
        predictor_repo = PredictorRepository(session)
        stock_repo = StockRepository(session)

        created_prediction_id = None

        for extracted in result.predictions:
            # Resolve or create predictor
            slug = _slugify(extracted.predictor_name)
            predictor = await predictor_repo.get_by_slug(slug)
            if predictor is None:
                predictor = Predictor(
                    name=extracted.predictor_name,
                    slug=slug,
                    type="individual",
                )
                predictor = await predictor_repo.create(predictor)

            # Resolve stock by symbol
            stock = await stock_repo.get_by_symbol(extracted.stock_symbol)
            if stock is None:
                logger.warning("Stock %s not found, skipping prediction", extracted.stock_symbol)
                continue

            from datetime import date
            from decimal import Decimal

            from app.services.prediction import _compute_default_eval_date

            prediction_date = date.today()
            default_eval_date = _compute_default_eval_date(prediction_date, None)

            prediction = Prediction(
                predictor_id=predictor.id,
                stock_id=stock.id,
                target_price=Decimal(str(extracted.target_price)),
                price_at_prediction=Decimal(str(extracted.current_price_mentioned or 0)),
                prediction_date=prediction_date,
                default_eval_date=default_eval_date,
                source_url=url,
                source_type=extracted.source_type,
                raw_quote=extracted.raw_quote,
                submitted_by=uuid.UUID(reviewer_id),
                extraction_method="ai_auto",
                ai_confidence=Decimal(str(extracted.confidence)),
                status="pending_review",
            )
            prediction = await pred_repo.create(prediction)
            if created_prediction_id is None:
                created_prediction_id = prediction.id

        # Update suggestion if applicable
        if suggestion_id and created_prediction_id:
            suggestion_repo = SuggestionRepository(session)
            suggestion = await suggestion_repo.get_by_id(uuid.UUID(suggestion_id))
            if suggestion:
                suggestion.promoted_to = created_prediction_id
                await session.flush()

        await session.commit()


@celery_app.task(name="extract_prediction_task", bind=True, max_retries=2)
def extract_prediction_task(self, suggestion_id: str | None, reviewer_id: str, url: str) -> dict[str, str]:  # type: ignore[no-untyped-def]
    """Extract predictions from URL and create DB records."""
    try:
        asyncio.run(_run_extraction(suggestion_id, reviewer_id, url))
        return {"status": "ok", "url": url}
    except Exception as exc:
        logger.exception("Extraction task failed for %s", url)
        raise self.retry(exc=exc, countdown=30) from exc
