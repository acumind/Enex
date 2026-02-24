"""Integration tests for public predictor API routes."""

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import create_test_predictor


async def test_get_predictor_by_slug(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_test_predictor(db_session, name="Test Analyst", slug="test-analyst")

    resp = await client.get("/api/v1/predictors/test-analyst")
    assert resp.status_code == 200
    data = resp.json()
    assert data["slug"] == "test-analyst"
    assert data["name"] == "Test Analyst"


async def test_get_predictor_not_found(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/predictors/nonexistent")
    assert resp.status_code == 404


async def test_get_predictor_members(client: AsyncClient, db_session: AsyncSession) -> None:
    parent = await create_test_predictor(
        db_session, name="Firm", slug="firm", predictor_type="brokerage"
    )
    await create_test_predictor(db_session, name="Analyst A", parent_id=parent.id)
    await create_test_predictor(db_session, name="Analyst B", parent_id=parent.id)

    resp = await client.get("/api/v1/predictors/firm/members")
    assert resp.status_code == 200
    members = resp.json()
    assert len(members) == 2


async def test_get_predictor_predictions_empty(client: AsyncClient, db_session: AsyncSession) -> None:
    await create_test_predictor(db_session, name="No Preds", slug="no-preds")

    resp = await client.get("/api/v1/predictors/no-preds/predictions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["has_more"] is False
