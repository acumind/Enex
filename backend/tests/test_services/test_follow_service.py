"""Tests for FollowService."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.services.follow import FollowService
from tests.conftest import create_test_predictor, create_test_user


async def test_add_follow(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    service = FollowService(db_session)

    await service.add(user.id, predictor.id)
    assert await service.check(user.id, predictor.id) is True


async def test_add_predictor_not_found(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    service = FollowService(db_session)

    with pytest.raises(NotFoundError):
        await service.add(user.id, uuid.uuid4())


async def test_add_duplicate_raises_conflict(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    service = FollowService(db_session)

    await service.add(user.id, predictor.id)
    with pytest.raises(ConflictError):
        await service.add(user.id, predictor.id)


async def test_remove_follow(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    service = FollowService(db_session)

    await service.add(user.id, predictor.id)
    await service.remove(user.id, predictor.id)
    assert await service.check(user.id, predictor.id) is False


async def test_remove_not_following_raises_not_found(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    service = FollowService(db_session)

    with pytest.raises(NotFoundError):
        await service.remove(user.id, uuid.uuid4())


async def test_check_not_following(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    service = FollowService(db_session)

    assert await service.check(user.id, uuid.uuid4()) is False


async def test_list_following(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    predictor = await create_test_predictor(db_session)
    service = FollowService(db_session)

    await service.add(user.id, predictor.id)
    result = await service.list_following(user.id)

    assert len(result.items) == 1
    assert result.items[0].predictor_name == predictor.name
    assert result.has_more is False


async def test_list_following_empty(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    service = FollowService(db_session)

    result = await service.list_following(user.id)
    assert result.items == []
