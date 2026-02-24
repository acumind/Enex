"""OTP code data access repository."""

import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import OTPCode
from app.repositories.base import BaseRepository


class OTPRepository(BaseRepository[OTPCode]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, OTPCode)

    async def get_latest_unused(self, identifier: str, purpose: str) -> OTPCode | None:
        result = await self.session.execute(
            select(OTPCode)
            .where(
                OTPCode.identifier == identifier,
                OTPCode.purpose == purpose,
                OTPCode.used_at.is_(None),
                OTPCode.expires_at > func.now(),
            )
            .order_by(OTPCode.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def increment_attempts(self, otp_id: uuid.UUID) -> None:
        await self.session.execute(update(OTPCode).where(OTPCode.id == otp_id).values(attempts=OTPCode.attempts + 1))
        await self.session.flush()

    async def mark_used(self, otp_id: uuid.UUID) -> None:
        await self.session.execute(update(OTPCode).where(OTPCode.id == otp_id).values(used_at=func.now()))
        await self.session.flush()

    async def invalidate_all(self, identifier: str, purpose: str) -> None:
        await self.session.execute(
            update(OTPCode)
            .where(
                OTPCode.identifier == identifier,
                OTPCode.purpose == purpose,
                OTPCode.used_at.is_(None),
            )
            .values(used_at=func.now())
        )
        await self.session.flush()

    async def count_recent(self, identifier: str, purpose: str, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count())
            .select_from(OTPCode)
            .where(
                OTPCode.identifier == identifier,
                OTPCode.purpose == purpose,
                OTPCode.created_at >= since,
            )
        )
        return result.scalar_one()
