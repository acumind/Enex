"""Tests for OTPRepository CRUD, expiry, attempts, invalidation."""

from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.otp import OTPRepository
from tests.conftest import create_test_otp


async def test_get_latest_unused(db_session: AsyncSession) -> None:
    otp = await create_test_otp(db_session, identifier="a@b.com", code="111111")
    repo = OTPRepository(db_session)
    found = await repo.get_latest_unused("a@b.com", "login")
    assert found is not None
    assert found.id == otp.id


async def test_get_latest_unused_skips_used(db_session: AsyncSession) -> None:
    now = datetime.now(UTC).replace(tzinfo=None)
    await create_test_otp(db_session, identifier="a@b.com", code="111111", used_at=now)
    repo = OTPRepository(db_session)
    found = await repo.get_latest_unused("a@b.com", "login")
    assert found is None


async def test_get_latest_unused_skips_expired(db_session: AsyncSession) -> None:
    await create_test_otp(
        db_session,
        identifier="a@b.com",
        code="111111",
        expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(minutes=1),
    )
    repo = OTPRepository(db_session)
    found = await repo.get_latest_unused("a@b.com", "login")
    assert found is None


async def test_increment_attempts(db_session: AsyncSession) -> None:
    otp = await create_test_otp(db_session, identifier="a@b.com")
    repo = OTPRepository(db_session)
    await repo.increment_attempts(otp.id)
    await db_session.refresh(otp)
    assert otp.attempts == 1


async def test_mark_used(db_session: AsyncSession) -> None:
    otp = await create_test_otp(db_session, identifier="a@b.com")
    repo = OTPRepository(db_session)
    await repo.mark_used(otp.id)
    await db_session.refresh(otp)
    assert otp.used_at is not None


async def test_invalidate_all(db_session: AsyncSession) -> None:
    await create_test_otp(db_session, identifier="a@b.com", code="111111")
    await create_test_otp(db_session, identifier="a@b.com", code="222222")
    repo = OTPRepository(db_session)
    await repo.invalidate_all("a@b.com", "login")
    found = await repo.get_latest_unused("a@b.com", "login")
    assert found is None


async def test_count_recent(db_session: AsyncSession) -> None:
    await create_test_otp(db_session, identifier="a@b.com", code="111111")
    await create_test_otp(db_session, identifier="a@b.com", code="222222")
    repo = OTPRepository(db_session)
    count = await repo.count_recent("a@b.com", "login", datetime.now(UTC).replace(tzinfo=None) - timedelta(hours=1))
    assert count == 2
