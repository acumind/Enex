"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "enex",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

celery_app.conf.beat_schedule = {
    "fetch-daily-prices": {
        "task": "fetch_daily_prices_task",
        "schedule": crontab(hour=23, minute=0),  # 23:00 IST daily
    },
    "evaluate-predictions": {
        "task": "evaluate_predictions_task",
        "schedule": crontab(hour=23, minute=30),  # 23:30 IST daily
    },
    "update-scorecards": {
        "task": "update_scorecards_task",
        "schedule": crontab(hour=23, minute=45),  # 23:45 IST daily
    },
}

celery_app.autodiscover_tasks(["app.jobs"])
