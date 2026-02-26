"""Lightweight Redis-based tracker for recent Celery task IDs."""

import contextlib
import logging
import time

import redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_SORTED_SET_KEY = "enex:recent_tasks"
_MAX_TRACKED = 200


def _get_redis_client() -> redis.Redis:
    settings = get_settings()
    return redis.from_url(settings.REDIS_URL, decode_responses=True)


def track_task(task_id: str, task_name: str) -> None:
    """Track a task ID in a Redis sorted set (called from within Celery tasks)."""
    try:
        r = _get_redis_client()
        # Store as "task_id:task_name" with timestamp score
        member = f"{task_id}:{task_name}"
        r.zadd(_SORTED_SET_KEY, {member: time.time()})
        # Trim to keep only the most recent entries
        r.zremrangebyrank(_SORTED_SET_KEY, 0, -(_MAX_TRACKED + 1))
    except Exception:
        logger.warning("Failed to track task %s", task_id)


def get_recent_tasks(limit: int = 50) -> list[dict]:
    """Fetch recent task statuses from Redis + Celery result backend."""
    from app.jobs.celery_app import celery_app

    try:
        r = _get_redis_client()
        members = r.zrevrange(_SORTED_SET_KEY, 0, limit - 1)
    except Exception:
        logger.warning("Failed to read recent tasks from Redis")
        return []

    results = []
    for member in members:
        parts = member.split(":", 1)
        if len(parts) != 2:
            continue
        task_id, task_name = parts

        async_result = celery_app.AsyncResult(task_id)
        entry = {
            "task_id": task_id,
            "task_name": task_name,
            "status": async_result.status,
            "result": None,
            "date_done": None,
            "traceback": None,
        }

        if async_result.date_done:
            entry["date_done"] = async_result.date_done.isoformat()

        if async_result.successful():
            with contextlib.suppress(Exception):
                entry["result"] = async_result.result
        elif async_result.failed():
            entry["traceback"] = str(async_result.traceback) if async_result.traceback else None

        results.append(entry)

    return results
