"""Celery tasks for dispatching notifications."""

import asyncio
import logging

from app.jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _dispatch_outcome_notifications(prediction_ids: list[str]) -> int:
    import uuid

    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.models.notification import Notification
    from app.models.prediction import Prediction
    from app.models.stock import Stock
    from app.repositories.notification import NotificationRepository
    from app.repositories.watchlist import WatchlistRepository

    created = 0

    async with async_session_factory() as session:
        watchlist_repo = WatchlistRepository(session)
        notification_repo = NotificationRepository(session)

        for pid_str in prediction_ids:
            pid = uuid.UUID(pid_str)
            stmt = select(Prediction, Stock).join(Stock, Prediction.stock_id == Stock.id).where(Prediction.id == pid)
            result = await session.execute(stmt)
            row = result.first()
            if row is None:
                continue

            prediction, stock = row

            user_ids = await watchlist_repo.list_users_watching_stock(stock.id)

            notifications = [
                Notification(
                    user_id=uid,
                    type="prediction_outcome",
                    title=f"Prediction outcome for {stock.symbol}",
                    message=f"A prediction for {stock.name} ({stock.symbol}) has been evaluated.",
                    data={"stock_symbol": stock.symbol, "prediction_id": pid_str},
                )
                for uid in user_ids
            ]

            if notifications:
                count = await notification_repo.create_bulk(notifications)
                created += count

        await session.commit()

    return created


async def _dispatch_new_prediction_notifications(prediction_id: str) -> int:
    import uuid

    from sqlalchemy import select

    from app.core.database import async_session_factory
    from app.models.notification import Notification
    from app.models.prediction import Prediction
    from app.models.predictor import Predictor
    from app.models.stock import Stock
    from app.repositories.follow import FollowRepository
    from app.repositories.notification import NotificationRepository

    async with async_session_factory() as session:
        pid = uuid.UUID(prediction_id)
        stmt = (
            select(Prediction, Predictor, Stock)
            .join(Predictor, Prediction.predictor_id == Predictor.id)
            .join(Stock, Prediction.stock_id == Stock.id)
            .where(Prediction.id == pid)
        )
        result = await session.execute(stmt)
        row = result.first()
        if row is None:
            return 0

        prediction, predictor, stock = row

        follow_repo = FollowRepository(session)
        notification_repo = NotificationRepository(session)

        user_ids = await follow_repo.list_users_following_predictor(predictor.id)

        notifications = [
            Notification(
                user_id=uid,
                type="followed_predictor_new_prediction",
                title=f"New prediction by {predictor.name}",
                message=f"{predictor.name} made a new prediction for {stock.name} ({stock.symbol}).",
                data={
                    "predictor_slug": predictor.slug,
                    "stock_symbol": stock.symbol,
                    "prediction_id": prediction_id,
                },
            )
            for uid in user_ids
        ]

        created = 0
        if notifications:
            created = await notification_repo.create_bulk(notifications)

        await session.commit()

    return created


@celery_app.task(name="dispatch_outcome_notifications_task")
def dispatch_outcome_notifications_task(prediction_ids: list[str]) -> dict[str, int]:
    """Create notifications for users watching stocks with evaluated predictions."""
    try:
        created = asyncio.run(_dispatch_outcome_notifications(prediction_ids))
        logger.info("Dispatched %d outcome notifications", created)
        return {"notifications_created": created}
    except Exception:
        logger.exception("Failed to dispatch outcome notifications")
        return {"notifications_created": 0}


@celery_app.task(name="dispatch_new_prediction_notifications_task")
def dispatch_new_prediction_notifications_task(prediction_id: str) -> dict[str, int]:
    """Create notifications for users following the predictor of a new prediction."""
    try:
        created = asyncio.run(_dispatch_new_prediction_notifications(prediction_id))
        logger.info("Dispatched %d new-prediction notifications", created)
        return {"notifications_created": created}
    except Exception:
        logger.exception("Failed to dispatch new prediction notifications")
        return {"notifications_created": 0}
