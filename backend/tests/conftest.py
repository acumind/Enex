"""Test configuration: async DB engine, per-test transaction rollback, test client."""

import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import get_settings
from app.core.database import get_db
from app.main import app
from app.models.base import Base

settings = get_settings()

# Use a separate test database — same PostgreSQL, different DB name
# Only replace the database name (last path segment), not the username
_base_url = settings.DATABASE_URL.rsplit("/", 1)[0]
_test_async_url = f"{_base_url}/enex_test"
# Sync URL for DDL operations (create_all / drop_all) — avoids event loop issues
_test_sync_url = _test_async_url.replace("+asyncpg", "")


@pytest.fixture(scope="session", autouse=True)
def _setup_db() -> None:
    """Create all tables once per test session using sync engine, drop after."""
    sync_engine = create_engine(_test_sync_url)
    Base.metadata.create_all(sync_engine)
    yield  # type: ignore[misc]
    Base.metadata.drop_all(sync_engine)
    sync_engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Per-test session wrapped in a transaction that rolls back after each test."""
    engine = create_async_engine(_test_async_url, echo=False)
    async with engine.connect() as conn:
        txn = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await txn.rollback()
    await engine.dispose()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Test HTTP client with DB dependency overridden to use rollback session."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

async def create_test_user(
    db_session: AsyncSession,
    *,
    email: str | None = None,
    phone: str | None = None,
    role: str = "user",
    is_active: bool = True,
    name: str | None = None,
) -> "User":  # type: ignore[name-defined]  # noqa: F821
    from app.models.user import User

    user = User(
        id=uuid.uuid4(),
        email=email or f"test-{uuid.uuid4().hex[:8]}@example.com",
        phone=phone,
        name=name or "Test User",
        role=role,
        is_active=is_active,
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def create_test_admin(
    db_session: AsyncSession,
    *,
    email: str | None = None,
) -> "User":  # type: ignore[name-defined]  # noqa: F821
    return await create_test_user(db_session, email=email, role="admin", name="Test Admin")


async def create_test_predictor(
    db_session: AsyncSession,
    *,
    name: str = "Test Analyst",
    slug: str | None = None,
    predictor_type: str = "individual",
    parent_id: uuid.UUID | None = None,
) -> "Predictor":  # type: ignore[name-defined]  # noqa: F821
    from app.models.predictor import Predictor

    predictor = Predictor(
        id=uuid.uuid4(),
        name=name,
        slug=slug or f"test-analyst-{uuid.uuid4().hex[:8]}",
        type=predictor_type,
        parent_id=parent_id,
    )
    db_session.add(predictor)
    await db_session.flush()
    return predictor


async def create_test_stock(
    db_session: AsyncSession,
    *,
    symbol: str | None = None,
    name: str = "Test Company Ltd",
    exchange: str = "NSE",
    sector: str | None = "Technology",
) -> "Stock":  # type: ignore[name-defined]  # noqa: F821
    from app.models.stock import Stock

    stock = Stock(
        id=uuid.uuid4(),
        symbol=symbol or f"TST{uuid.uuid4().hex[:4].upper()}",
        name=name,
        exchange=exchange,
        sector=sector,
    )
    db_session.add(stock)
    await db_session.flush()
    return stock


async def create_test_suggestion(
    db_session: AsyncSession,
    *,
    user_id: uuid.UUID | None = None,
    url: str = "https://example.com/suggestion",
    note: str | None = "Check this prediction",
) -> "PredictionSuggestion":  # type: ignore[name-defined]  # noqa: F821
    from app.models.prediction import PredictionSuggestion

    if user_id is None:
        user = await create_test_user(db_session)
        user_id = user.id

    suggestion = PredictionSuggestion(
        id=uuid.uuid4(),
        url=url,
        note=note,
        submitted_by=user_id,
        status="pending",
    )
    db_session.add(suggestion)
    await db_session.flush()
    return suggestion
