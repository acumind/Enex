"""Prediction business logic: creation, review queue, approve/reject."""

import calendar
import logging
import uuid
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleViolation, ConflictError, NotFoundError
from app.models.prediction import Prediction, PredictionOutcome
from app.repositories.prediction import PredictionRepository
from app.repositories.predictor import PredictorRepository
from app.repositories.stock import StockRepository
from app.schemas.common import PaginatedResponse
from app.schemas.prediction import PredictionCreate, PredictionResponse, PredictionUpdate

logger = logging.getLogger(__name__)


def _add_months(d: date, months: int) -> date:
    """Add months to a date, clamping day to month's last day."""
    month = d.month - 1 + months
    year = d.year + month // 12
    month = month % 12 + 1
    day = min(d.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _compute_default_eval_date(prediction_date: date, target_date: date | None) -> date:
    """target_date if given, else prediction_date + 12 months."""
    if target_date is not None:
        return target_date
    return _add_months(prediction_date, 12)


class PredictionService:
    def __init__(self, session: AsyncSession) -> None:
        self.pred_repo = PredictionRepository(session)
        self.predictor_repo = PredictorRepository(session)
        self.stock_repo = StockRepository(session)

    async def create(self, data: PredictionCreate, submitted_by: uuid.UUID | None = None) -> PredictionResponse:
        # Verify predictor exists
        predictor = await self.predictor_repo.get_by_id(data.predictor_id)
        if predictor is None:
            raise NotFoundError("Predictor not found")

        # Verify stock exists
        stock = await self.stock_repo.get_by_id(data.stock_id)
        if stock is None:
            raise NotFoundError("Stock not found")

        # Duplicate detection
        duplicate = await self.pred_repo.find_duplicate(
            data.predictor_id,
            data.stock_id,
            data.target_price,
            data.prediction_date,
        )
        if duplicate is not None:
            raise ConflictError("A similar prediction already exists for this predictor, stock, and target price")

        default_eval_date = _compute_default_eval_date(data.prediction_date, data.target_date)

        prediction = Prediction(
            predictor_id=data.predictor_id,
            stock_id=data.stock_id,
            target_price=data.target_price,
            price_at_prediction=data.price_at_prediction,
            prediction_date=data.prediction_date,
            target_date=data.target_date,
            default_eval_date=default_eval_date,
            source_url=data.source_url,
            source_type=data.source_type,
            raw_quote=data.raw_quote,
            submitted_by=submitted_by,
            extraction_method=data.extraction_method,
            ai_confidence=data.ai_confidence,
            status="pending_review",
        )
        prediction = await self.pred_repo.create(prediction)

        # Dispatch background archival
        try:
            from app.jobs.archive import archive_url_task

            archive_url_task.delay(str(prediction.id), data.source_url)
        except Exception:
            logger.warning("Failed to dispatch archive task for prediction %s", prediction.id)

        return PredictionResponse.model_validate(prediction)

    async def update(
        self, prediction_id: uuid.UUID, data: PredictionUpdate, editor_id: uuid.UUID
    ) -> PredictionResponse:
        prediction = await self.pred_repo.get_by_id(prediction_id)
        if prediction is None:
            raise NotFoundError("Prediction not found")

        # Block editing evaluated predictions
        from sqlalchemy import select

        outcome = await self.pred_repo.session.scalar(
            select(PredictionOutcome).where(PredictionOutcome.prediction_id == prediction_id)
        )
        if outcome is not None:
            raise BusinessRuleViolation("Cannot edit an evaluated prediction")

        update_dict = data.model_dump(exclude_unset=True)

        # Recalculate default_eval_date if dates changed
        if "prediction_date" in update_dict or "target_date" in update_dict:
            p_date = update_dict.get("prediction_date", prediction.prediction_date)
            t_date = update_dict.get("target_date", prediction.target_date)
            update_dict["default_eval_date"] = _compute_default_eval_date(p_date, t_date)

        prediction = await self.pred_repo.update(prediction, update_dict)
        return PredictionResponse.model_validate(prediction)

    async def approve(self, prediction_id: uuid.UUID, reviewer_id: uuid.UUID) -> PredictionResponse:
        prediction = await self.pred_repo.get_by_id(prediction_id)
        if prediction is None:
            raise NotFoundError("Prediction not found")
        if prediction.status != "pending_review":
            raise BusinessRuleViolation(f"Cannot approve prediction with status '{prediction.status}'")

        prediction = await self.pred_repo.approve(prediction, reviewer_id)

        # Dispatch notification for followers of this predictor
        try:
            from app.jobs.notifications import dispatch_new_prediction_notifications_task

            dispatch_new_prediction_notifications_task.delay(str(prediction.id))
        except Exception:
            logger.warning("Failed to dispatch new prediction notification for %s", prediction.id)

        return PredictionResponse.model_validate(prediction)

    async def reject(self, prediction_id: uuid.UUID, reviewer_id: uuid.UUID) -> PredictionResponse:
        prediction = await self.pred_repo.get_by_id(prediction_id)
        if prediction is None:
            raise NotFoundError("Prediction not found")
        if prediction.status != "pending_review":
            raise BusinessRuleViolation(f"Cannot reject prediction with status '{prediction.status}'")

        prediction = await self.pred_repo.reject(prediction, reviewer_id)
        return PredictionResponse.model_validate(prediction)

    async def bulk_approve(self, prediction_ids: list[uuid.UUID], reviewer_id: uuid.UUID) -> tuple[int, int, list[str]]:
        updated = 0
        failed = 0
        errors: list[str] = []
        for pid in prediction_ids:
            try:
                await self.approve(pid, reviewer_id=reviewer_id)
                updated += 1
            except Exception as e:
                failed += 1
                errors.append(f"{pid}: {e}")
        return updated, failed, errors

    async def bulk_reject(self, prediction_ids: list[uuid.UUID], reviewer_id: uuid.UUID) -> tuple[int, int, list[str]]:
        updated = 0
        failed = 0
        errors: list[str] = []
        for pid in prediction_ids:
            try:
                await self.reject(pid, reviewer_id=reviewer_id)
                updated += 1
            except Exception as e:
                failed += 1
                errors.append(f"{pid}: {e}")
        return updated, failed, errors

    async def list_review_queue(
        self,
        *,
        status: str = "pending_review",
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[PredictionResponse]:
        predictions = await self.pred_repo.list_by_status(status, cursor=cursor, limit=limit + 1)
        has_more = len(predictions) > limit
        if has_more:
            predictions = predictions[:limit]

        items = [PredictionResponse.model_validate(p) for p in predictions]
        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[PredictionResponse](items=items, next_cursor=next_cursor, has_more=has_more)

    async def list_recent(
        self,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[PredictionResponse]:
        predictions = await self.pred_repo.list_recent(cursor=cursor, limit=limit + 1)
        has_more = len(predictions) > limit
        if has_more:
            predictions = predictions[:limit]

        items = [PredictionResponse.model_validate(p) for p in predictions]
        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[PredictionResponse](items=items, next_cursor=next_cursor, has_more=has_more)

    async def list_by_predictor(
        self,
        predictor_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[PredictionResponse]:
        predictions = await self.pred_repo.list_by_predictor(predictor_id, cursor=cursor, limit=limit + 1)
        has_more = len(predictions) > limit
        if has_more:
            predictions = predictions[:limit]

        items = [PredictionResponse.model_validate(p) for p in predictions]
        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[PredictionResponse](items=items, next_cursor=next_cursor, has_more=has_more)

    async def list_by_stock(
        self,
        stock_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[PredictionResponse]:
        predictions = await self.pred_repo.list_by_stock(stock_id, cursor=cursor, limit=limit + 1)
        has_more = len(predictions) > limit
        if has_more:
            predictions = predictions[:limit]

        items = [PredictionResponse.model_validate(p) for p in predictions]
        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[PredictionResponse](items=items, next_cursor=next_cursor, has_more=has_more)

    async def list_by_stock_enriched(
        self,
        stock_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[PredictionResponse]:
        rows = await self.pred_repo.list_by_stock_enriched(stock_id, cursor=cursor, limit=limit + 1)
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = []
        for prediction, predictor_name, predictor_slug in rows:
            resp = PredictionResponse.model_validate(prediction)
            resp.predictor_name = predictor_name
            resp.predictor_slug = predictor_slug
            items.append(resp)

        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[PredictionResponse](items=items, next_cursor=next_cursor, has_more=has_more)

    async def list_by_predictor_enriched(
        self,
        predictor_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[PredictionResponse]:
        rows = await self.pred_repo.list_by_predictor_enriched(predictor_id, cursor=cursor, limit=limit + 1)
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = []
        for prediction, stock_symbol, stock_name in rows:
            resp = PredictionResponse.model_validate(prediction)
            resp.stock_symbol = stock_symbol
            resp.stock_name = stock_name
            items.append(resp)

        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[PredictionResponse](items=items, next_cursor=next_cursor, has_more=has_more)

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[PredictionResponse]:
        predictions = await self.pred_repo.list_by_user(user_id, cursor=cursor, limit=limit + 1)
        has_more = len(predictions) > limit
        if has_more:
            predictions = predictions[:limit]

        items = [PredictionResponse.model_validate(p) for p in predictions]
        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[PredictionResponse](items=items, next_cursor=next_cursor, has_more=has_more)
