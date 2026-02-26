"""Audit log repository."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.base import BaseRepository


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AuditLog)

    async def list_recent(
        self,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> list[tuple[AuditLog, str | None]]:
        stmt = (
            select(AuditLog, User.name)
            .outerjoin(User, AuditLog.actor_id == User.id)
            .order_by(AuditLog.created_at.desc())
        )
        if cursor is not None:
            stmt = stmt.where(AuditLog.created_at < cursor)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return list(result.all())
