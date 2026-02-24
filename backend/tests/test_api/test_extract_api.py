"""Integration tests for /extract API route — auth, rate limit, mock extraction."""

import uuid
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.schemas.extraction import ExtractionResponse, ExtractionResult
from tests.conftest import create_test_user


def _auth_header(user_id: uuid.UUID, role: str = "user") -> dict[str, str]:
    token = create_access_token(user_id, role)
    return {"Authorization": f"Bearer {token}"}


async def test_extract_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/v1/extract", json={"url": "https://example.com"})
    assert resp.status_code in (401, 403)


async def test_extract_validates_url(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)
    resp = await client.post(
        "/api/v1/extract",
        json={"url": "not-a-url"},
        headers=_auth_header(user.id),
    )
    assert resp.status_code == 422


async def test_extract_success(client: AsyncClient, db_session: AsyncSession) -> None:
    user = await create_test_user(db_session)

    mock_response = ExtractionResponse(
        url="https://example.com/article",
        predictions=[
            ExtractionResult(
                predictor_name="Test Analyst",
                stock_name="Test Corp",
                stock_symbol="TEST",
                target_price=1500.0,
                direction="buy",
                confidence=0.9,
                source_type="news_article",
            ),
        ],
        source_text_length=5000,
    )

    with patch(
        "app.api.routes.extract.ExtractionService.extract_from_url",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        resp = await client.post(
            "/api/v1/extract",
            json={"url": "https://example.com/article"},
            headers=_auth_header(user.id),
        )

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["predictions"]) == 1
    assert data["predictions"][0]["predictor_name"] == "Test Analyst"
    assert data["source_text_length"] == 5000
