"""Tests for SuggestionService — create, promote (with Celery mock), dismiss."""

from unittest.mock import patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleViolation, NotFoundError
from app.schemas.suggestion import SuggestionCreate
from app.services.suggestion import SuggestionService
from tests.conftest import create_test_user


async def test_create_suggestion(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    service = SuggestionService(db_session)

    data = SuggestionCreate(url="https://example.com/article", note="Good prediction here")
    result = await service.create(data, submitted_by=user.id)

    assert result.url == "https://example.com/article"
    assert result.note == "Good prediction here"
    assert result.submitted_by == user.id
    assert result.status == "pending"


async def test_list_pending(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    service = SuggestionService(db_session)

    # Create 3 suggestions
    for i in range(3):
        await service.create(
            SuggestionCreate(url=f"https://example.com/article-{i}"),
            submitted_by=user.id,
        )

    result = await service.list_pending(limit=10)
    assert len(result.items) == 3
    assert result.has_more is False


async def test_promote_dispatches_celery_task(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    reviewer = await create_test_user(db_session, role="admin")
    service = SuggestionService(db_session)

    data = SuggestionCreate(url="https://example.com/promote-me")
    suggestion = await service.create(data, submitted_by=user.id)

    with patch("app.jobs.extraction.extract_prediction_task") as mock_task:
        mock_task.delay.return_value = None
        result = await service.promote(suggestion.id, reviewer_id=reviewer.id)

    assert result.status == "promoted"
    assert result.reviewed_by == reviewer.id
    mock_task.delay.assert_called_once()


async def test_promote_nonexistent_raises(db_session: AsyncSession) -> None:
    import uuid

    reviewer = await create_test_user(db_session, role="admin")
    service = SuggestionService(db_session)

    with pytest.raises(NotFoundError):
        await service.promote(uuid.uuid4(), reviewer_id=reviewer.id)


async def test_promote_non_pending_raises(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    reviewer = await create_test_user(db_session, role="admin")
    service = SuggestionService(db_session)

    data = SuggestionCreate(url="https://example.com/already-dismissed")
    suggestion = await service.create(data, submitted_by=user.id)

    # Dismiss it first
    await service.dismiss(suggestion.id, reviewer_id=reviewer.id)

    with pytest.raises(BusinessRuleViolation), patch("app.jobs.extraction.extract_prediction_task"):
        await service.promote(suggestion.id, reviewer_id=reviewer.id)


async def test_dismiss(db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    reviewer = await create_test_user(db_session, role="admin")
    service = SuggestionService(db_session)

    data = SuggestionCreate(url="https://example.com/dismiss-me")
    suggestion = await service.create(data, submitted_by=user.id)

    result = await service.dismiss(suggestion.id, reviewer_id=reviewer.id)
    assert result.status == "dismissed"
    assert result.reviewed_by == reviewer.id
    assert result.reviewed_at is not None


async def test_dismiss_nonexistent_raises(db_session: AsyncSession) -> None:
    import uuid

    reviewer = await create_test_user(db_session, role="admin")
    service = SuggestionService(db_session)

    with pytest.raises(NotFoundError):
        await service.dismiss(uuid.uuid4(), reviewer_id=reviewer.id)
