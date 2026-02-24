"""Tests for PredictorRepository CRUD and queries."""

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.predictor import PredictorRepository
from tests.conftest import create_test_predictor


async def test_get_by_slug(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session, name="Test Firm", slug="test-firm")
    repo = PredictorRepository(db_session)
    found = await repo.get_by_slug("test-firm")
    assert found is not None
    assert found.id == predictor.id


async def test_get_by_slug_not_found(db_session: AsyncSession) -> None:
    repo = PredictorRepository(db_session)
    assert await repo.get_by_slug("nonexistent") is None


async def test_slug_exists(db_session: AsyncSession) -> None:
    await create_test_predictor(db_session, slug="exists-slug")
    repo = PredictorRepository(db_session)
    assert await repo.slug_exists("exists-slug") is True
    assert await repo.slug_exists("does-not-exist") is False


async def test_list_by_type(db_session: AsyncSession) -> None:
    await create_test_predictor(db_session, predictor_type="individual")
    await create_test_predictor(db_session, predictor_type="individual")
    await create_test_predictor(db_session, predictor_type="brokerage")

    repo = PredictorRepository(db_session)
    individuals = await repo.list_by_type("individual")
    assert len(individuals) == 2


async def test_list_members(db_session: AsyncSession) -> None:
    parent = await create_test_predictor(db_session, name="Firm", predictor_type="brokerage")
    await create_test_predictor(db_session, name="Analyst A", parent_id=parent.id)
    await create_test_predictor(db_session, name="Analyst B", parent_id=parent.id)

    repo = PredictorRepository(db_session)
    members = await repo.list_members(parent.id)
    assert len(members) == 2
    assert members[0].name == "Analyst A"  # ordered by name
    assert members[1].name == "Analyst B"


async def test_list_by_type_pagination(db_session: AsyncSession) -> None:
    base_time = datetime(2025, 6, 1)
    for i in range(5):
        p = await create_test_predictor(db_session, name=f"Analyst {i}", predictor_type="individual")
        p.created_at = base_time - timedelta(hours=i)
    await db_session.flush()

    repo = PredictorRepository(db_session)
    first = await repo.list_by_type("individual", limit=3)
    assert len(first) == 3

    cursor = first[-1].created_at
    second = await repo.list_by_type("individual", cursor=cursor, limit=3)
    assert len(second) == 2
