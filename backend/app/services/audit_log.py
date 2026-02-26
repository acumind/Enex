"""Audit log service for recording and listing admin actions."""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.repositories.audit_log import AuditLogRepository
from app.schemas.audit_log import AuditLogResponse
from app.schemas.common import PaginatedResponse


class AuditLogService:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = AuditLogRepository(session)

    async def record(
        self,
        actor_id: uuid.UUID,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID | None = None,
        details: dict | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor_id=actor_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
        return await self.repo.create(entry)

    async def list_recent(
        self,
        *,
        cursor: datetime | None = None,
        limit: int = 20,
    ) -> PaginatedResponse[AuditLogResponse]:
        rows = await self.repo.list_recent(cursor=cursor, limit=limit + 1)
        has_more = len(rows) > limit
        if has_more:
            rows = rows[:limit]

        items = []
        for audit_log, actor_name in rows:
            resp = AuditLogResponse.model_validate(audit_log)
            resp.actor_name = actor_name
            items.append(resp)

        next_cursor = items[-1].created_at if has_more and items else None
        return PaginatedResponse[AuditLogResponse](items=items, next_cursor=next_cursor, has_more=has_more)
