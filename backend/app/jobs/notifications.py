"""Celery tasks for dispatching notifications."""

import asyncio
import logging

from app.jobs.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _send_outcome_emails(
    session,  # type: ignore[no-untyped-def]
    user_ids: list,
    stock_symbol: str,
    stock_name: str,
    prediction_id: str,
) -> None:
    """Send outcome emails to verified-email users (best-effort)."""
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.NOTIFICATION_EMAIL_ENABLED:
        return

    from sqlalchemy import select

    from app.integrations.email.resend_adapter import ResendAdapter
    from app.integrations.email.templates import prediction_outcome_email
    from app.models.prediction import PredictionOutcome
    from app.models.user import User

    # Fetch outcome status
    stmt = select(PredictionOutcome.outcome_status).where(PredictionOutcome.prediction_id == prediction_id)
    result = await session.execute(stmt)
    row = result.scalar_one_or_none()
    outcome_status = row if row else "evaluated"

    # Fetch users with verified emails
    stmt = select(User).where(
        User.id.in_(user_ids),
        User.is_email_verified.is_(True),
        User.email.isnot(None),
    )
    result = await session.execute(stmt)
    users = result.scalars().all()

    if not users:
        return

    subject, html_body = prediction_outcome_email(stock_symbol, stock_name, outcome_status)
    adapter = ResendAdapter()
    for user in users:
        try:
            await adapter.send_notification(user.email, subject, html_body)
        except Exception:
            logger.exception("Failed to send outcome email to user %s", user.id)


async def _send_new_prediction_emails(
    session,  # type: ignore[no-untyped-def]
    user_ids: list,
    predictor_name: str,
    predictor_slug: str,
    stock_symbol: str,
    stock_name: str,
) -> None:
    """Send new-prediction emails to verified-email users (best-effort)."""
    from app.core.config import get_settings

    settings = get_settings()
    if not settings.NOTIFICATION_EMAIL_ENABLED:
        return

    from sqlalchemy import select

    from app.integrations.email.resend_adapter import ResendAdapter
    from app.integrations.email.templates import new_prediction_email
    from app.models.user import User

    stmt = select(User).where(
        User.id.in_(user_ids),
        User.is_email_verified.is_(True),
        User.email.isnot(None),
    )
    result = await session.execute(stmt)
    users = result.scalars().all()

    if not users:
        return

    subject, html_body = new_prediction_email(predictor_name, predictor_slug, stock_symbol, stock_name)
    adapter = ResendAdapter()
    for user in users:
        try:
            await adapter.send_notification(user.email, subject, html_body)
        except Exception:
            logger.exception("Failed to send new-prediction email to user %s", user.id)


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

            # Send email notifications (best-effort, after in-app notifications)
            await _send_outcome_emails(session, user_ids, stock.symbol, stock.name, pid)

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

        # Send email notifications (best-effort, after in-app notifications)
        await _send_new_prediction_emails(session, user_ids, predictor.name, predictor.slug, stock.symbol, stock.name)

        await session.commit()

    return created


@celery_app.task(name="dispatch_outcome_notifications_task")
def dispatch_outcome_notifications_task(prediction_ids: list[str]) -> dict[str, int]:
    """Create notifications for users watching stocks with evaluated predictions."""
    from app.jobs.task_tracker import track_task

    track_task(dispatch_outcome_notifications_task.request.id, "dispatch_outcome_notifications")
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
    from app.jobs.task_tracker import track_task

    track_task(dispatch_new_prediction_notifications_task.request.id, "dispatch_new_prediction_notifications")
    try:
        created = asyncio.run(_dispatch_new_prediction_notifications(prediction_id))
        logger.info("Dispatched %d new-prediction notifications", created)
        return {"notifications_created": created}
    except Exception:
        logger.exception("Failed to dispatch new prediction notifications")
        return {"notifications_created": 0}
