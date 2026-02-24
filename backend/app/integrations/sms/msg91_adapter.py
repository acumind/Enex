"""MSG91 SMS adapter for OTP delivery."""

import logging

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

MSG91_API_URL = "https://control.msg91.com/api/v5/otp"


class MSG91Adapter:
    async def send_otp(self, phone: str, otp_code: str) -> bool:
        settings = get_settings()
        if not settings.MSG91_AUTH_KEY:
            logger.warning("MSG91_AUTH_KEY not configured, skipping SMS send")
            return False

        # MSG91 expects phone without '+' prefix
        mobile = phone.lstrip("+")

        payload = {
            "template_id": settings.MSG91_TEMPLATE_ID,
            "mobile": mobile,
            "sender_id": settings.MSG91_SENDER_ID,
            "otp": otp_code,
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    MSG91_API_URL,
                    json=payload,
                    headers={
                        "authkey": settings.MSG91_AUTH_KEY,
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )
                if resp.status_code >= 400:
                    logger.error("MSG91 API error: %s %s", resp.status_code, resp.text)
                    return False
                return True
        except httpx.HTTPError:
            logger.exception("Failed to send SMS via MSG91")
            return False
