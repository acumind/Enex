"""Resend email adapter for OTP delivery."""

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


class ResendAdapter:
    async def send_otp(self, to: str, otp_code: str) -> bool:
        settings = get_settings()
        if not settings.RESEND_API_KEY:
            logger.warning("RESEND_API_KEY not configured, skipping email send")
            return False

        payload = {
            "from": settings.RESEND_FROM_EMAIL,
            "to": [to],
            "subject": "Your Enex login code",
            "html": (
                f"<p>Your verification code is: <strong>{otp_code}</strong></p>"
                f"<p>This code expires in 5 minutes. Do not share it with anyone.</p>"
            ),
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    RESEND_API_URL,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )
                if resp.status_code >= 400:
                    logger.error("Resend API error: %s %s", resp.status_code, resp.text)
                    return False
                return True
        except httpx.HTTPError:
            logger.exception("Failed to send email via Resend")
            return False
