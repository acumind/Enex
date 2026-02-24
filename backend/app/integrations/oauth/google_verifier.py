"""Google OAuth token verification."""

import logging
from dataclasses import dataclass

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


@dataclass
class GoogleUserInfo:
    email: str
    name: str | None
    picture: str | None
    google_id: str


class GoogleVerifier:
    async def verify_id_token(self, id_token: str) -> GoogleUserInfo | None:
        """Verify a Google ID token via the tokeninfo endpoint."""
        settings = get_settings()
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    GOOGLE_TOKENINFO_URL,
                    params={"id_token": id_token},
                    timeout=10.0,
                )
                if resp.status_code != 200:
                    logger.warning("Google tokeninfo returned %s", resp.status_code)
                    return None

                data = resp.json()

                # Validate audience matches our client ID
                if data.get("aud") != settings.GOOGLE_CLIENT_ID:
                    logger.warning("Google token audience mismatch")
                    return None

                email = data.get("email")
                if not email:
                    logger.warning("Google token missing email")
                    return None

                return GoogleUserInfo(
                    email=email,
                    name=data.get("name"),
                    picture=data.get("picture"),
                    google_id=data.get("sub", ""),
                )
        except httpx.HTTPError:
            logger.exception("Failed to verify Google ID token")
            return None

    async def verify_access_token(self, access_token: str) -> GoogleUserInfo | None:
        """Verify a Google access token via the userinfo endpoint (fallback)."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    GOOGLE_USERINFO_URL,
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10.0,
                )
                if resp.status_code != 200:
                    logger.warning("Google userinfo returned %s", resp.status_code)
                    return None

                data = resp.json()
                email = data.get("email")
                if not email:
                    logger.warning("Google userinfo missing email")
                    return None

                return GoogleUserInfo(
                    email=email,
                    name=data.get("name"),
                    picture=data.get("picture"),
                    google_id=data.get("sub", ""),
                )
        except httpx.HTTPError:
            logger.exception("Failed to verify Google access token")
            return None
