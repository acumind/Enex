"""Wayback Machine adapter — archives URLs via the Save Page Now API."""

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class WaybackAdapter:
    def __init__(self) -> None:
        settings = get_settings()
        self.enabled = settings.WAYBACK_ARCHIVAL_ENABLED
        self.timeout = settings.WAYBACK_TIMEOUT_SECONDS

    async def save_url(self, url: str) -> str | None:
        if not self.enabled:
            return None

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"https://web.archive.org/save/{url}",
                    follow_redirects=True,
                )
                if response.status_code in (200, 302):
                    location = response.headers.get("content-location") or response.headers.get("location")
                    if location:
                        return f"https://web.archive.org{location}"
                    return f"https://web.archive.org/web/latest/{url}"
                logger.warning("Wayback save returned status %d for %s", response.status_code, url)
        except Exception:
            logger.exception("Wayback archival failed for %s", url)

        return None
