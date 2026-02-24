"""Tests for PredictorService: slug generation, parent validation, CRUD."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleViolation, NotFoundError
from app.schemas.predictor import PredictorCreate, PredictorUpdate
from app.services.predictor import PredictorService, _generate_slug
from tests.conftest import create_test_predictor


def test_generate_slug_basic() -> None:
    assert _generate_slug("Motilal Oswal") == "motilal-oswal"


def test_generate_slug_special_chars() -> None:
    assert _generate_slug("HDFC Bank (India)") == "hdfc-bank-india"


def test_generate_slug_extra_spaces() -> None:
    assert _generate_slug("  Dr.  Reddys  ") == "dr-reddys"


async def test_create_predictor(db_session: AsyncSession) -> None:
    service = PredictorService(db_session)
    data = PredictorCreate(name="John Doe", type="individual")
    result = await service.create(data)
    assert result.name == "John Doe"
    assert result.slug == "john-doe"
    assert result.type == "individual"


async def test_create_predictor_slug_collision(db_session: AsyncSession) -> None:
    await create_test_predictor(db_session, name="Test", slug="test")

    service = PredictorService(db_session)
    data = PredictorCreate(name="Test", type="individual")
    result = await service.create(data)
    assert result.slug == "test-2"


async def test_create_predictor_with_parent(db_session: AsyncSession) -> None:
    parent = await create_test_predictor(db_session, predictor_type="brokerage")

    service = PredictorService(db_session)
    data = PredictorCreate(name="Analyst X", type="individual", parent_id=parent.id)
    result = await service.create(data)
    assert result.parent_id == parent.id


async def test_create_predictor_invalid_parent_type(db_session: AsyncSession) -> None:
    parent = await create_test_predictor(db_session, predictor_type="individual")

    service = PredictorService(db_session)
    data = PredictorCreate(name="Bad Child", type="individual", parent_id=parent.id)
    with pytest.raises(BusinessRuleViolation, match="Parent must be one of"):
        await service.create(data)


async def test_create_predictor_parent_not_found(db_session: AsyncSession) -> None:
    service = PredictorService(db_session)
    data = PredictorCreate(name="Orphan", type="individual", parent_id=uuid.uuid4())
    with pytest.raises(NotFoundError, match="Parent predictor not found"):
        await service.create(data)


async def test_update_predictor_renames_slug(db_session: AsyncSession) -> None:
    predictor = await create_test_predictor(db_session, name="Old Name", slug="old-name")

    service = PredictorService(db_session)
    result = await service.update(predictor.id, PredictorUpdate(name="New Name"))
    assert result.slug == "new-name"
    assert result.name == "New Name"


async def test_update_predictor_not_found(db_session: AsyncSession) -> None:
    service = PredictorService(db_session)
    with pytest.raises(NotFoundError):
        await service.update(uuid.uuid4(), PredictorUpdate(name="X"))


async def test_get_by_slug(db_session: AsyncSession) -> None:
    await create_test_predictor(db_session, name="Find Me", slug="find-me")

    service = PredictorService(db_session)
    result = await service.get_by_slug("find-me")
    assert result.name == "Find Me"


async def test_get_by_slug_not_found(db_session: AsyncSession) -> None:
    service = PredictorService(db_session)
    with pytest.raises(NotFoundError):
        await service.get_by_slug("nonexistent")


async def test_list_members(db_session: AsyncSession) -> None:
    parent = await create_test_predictor(db_session, name="Firm", slug="firm", predictor_type="brokerage")
    await create_test_predictor(db_session, name="Member A", parent_id=parent.id)
    await create_test_predictor(db_session, name="Member B", parent_id=parent.id)

    service = PredictorService(db_session)
    members = await service.list_members("firm")
    assert len(members) == 2
