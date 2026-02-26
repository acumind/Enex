"""Tests for AuditLogService: record and list operations."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.audit_log import AuditLogService
from tests.conftest import create_test_admin


async def test_record_creates_entry(db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    service = AuditLogService(db_session)

    entry = await service.record(
        actor_id=admin.id,
        action="stock.create",
        entity_type="stock",
        entity_id=uuid.uuid4(),
        details={"symbol": "RELIANCE"},
    )

    assert entry.id is not None
    assert entry.actor_id == admin.id
    assert entry.action == "stock.create"
    assert entry.entity_type == "stock"
    assert entry.details == {"symbol": "RELIANCE"}


async def test_record_without_entity_id(db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    service = AuditLogService(db_session)

    entry = await service.record(
        actor_id=admin.id,
        action="evaluation.trigger",
        entity_type="prediction",
    )

    assert entry.entity_id is None
    assert entry.details is None


async def test_list_recent_returns_entries(db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    service = AuditLogService(db_session)

    for i in range(5):
        await service.record(admin.id, f"action.{i}", "test", details={"index": i})

    result = await service.list_recent(limit=3)

    assert len(result.items) == 3
    assert result.has_more is True
    assert result.next_cursor is not None
    # All items should have valid actions
    actions = {item.action for item in result.items}
    assert len(actions) == 3


async def test_list_recent_returns_all_when_no_more(db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session)
    service = AuditLogService(db_session)

    for i in range(3):
        await service.record(admin.id, f"action.{i}", "test")

    result = await service.list_recent(limit=10)
    assert len(result.items) == 3
    assert result.has_more is False


async def test_list_recent_enriches_actor_name(db_session: AsyncSession) -> None:
    admin = await create_test_admin(db_session, email="audit-admin@test.com")
    service = AuditLogService(db_session)

    await service.record(admin.id, "test.action", "test")

    result = await service.list_recent(limit=10)
    assert len(result.items) == 1
    assert result.items[0].actor_name == "Test Admin"
