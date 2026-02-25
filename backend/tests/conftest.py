"""Test configuration: async DB engine, per-test transaction rollback, test client."""

import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

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


async def create_test_otp(
    db_session: AsyncSession,
    *,
    identifier: str = "test@example.com",
    code: str = "123456",
    purpose: str = "login",
    hashed: bool = True,
    expires_at: datetime | None = None,
    used_at: datetime | None = None,
    attempts: int = 0,
) -> "OTPCode":  # type: ignore[name-defined]  # noqa: F821
    from app.core.security import hash_otp
    from app.models.user import OTPCode

    otp = OTPCode(
        id=uuid.uuid4(),
        identifier=identifier,
        code=hash_otp(code) if hashed else code,
        purpose=purpose,
        expires_at=expires_at or (datetime.now(UTC) + timedelta(minutes=5)).replace(tzinfo=None),
        used_at=used_at,
        attempts=attempts,
    )
    db_session.add(otp)
    await db_session.flush()
    return otp


async def create_test_prediction(
    db_session: AsyncSession,
    *,
    predictor_id: uuid.UUID,
    stock_id: uuid.UUID,
    target_price: Decimal = Decimal("1500.00"),
    price_at_prediction: Decimal = Decimal("1200.00"),
    prediction_date: date | None = None,
    default_eval_date: date | None = None,
    status: str = "approved",
    submitted_by: uuid.UUID | None = None,
) -> "Prediction":  # type: ignore[name-defined]  # noqa: F821
    from app.models.prediction import Prediction

    pred_date = prediction_date or date(2025, 1, 15)
    eval_date = default_eval_date or date(2026, 1, 15)

    prediction = Prediction(
        id=uuid.uuid4(),
        predictor_id=predictor_id,
        stock_id=stock_id,
        target_price=target_price,
        price_at_prediction=price_at_prediction,
        prediction_date=pred_date,
        default_eval_date=eval_date,
        source_url="https://example.com/article",
        source_type="news_article",
        status=status,
        submitted_by=submitted_by,
    )
    db_session.add(prediction)
    await db_session.flush()
    return prediction


async def create_test_outcome(
    db_session: AsyncSession,
    *,
    prediction_id: uuid.UUID,
    outcome_status: str = "hit",
    actual_price: Decimal = Decimal("1500.00"),
    highest_price: Decimal | None = Decimal("1600.00"),
    lowest_price: Decimal | None = Decimal("1100.00"),
    deviation_pct: Decimal = Decimal("0.00"),
    evaluation_date: date | None = None,
) -> "PredictionOutcome":  # type: ignore[name-defined]  # noqa: F821
    from app.models.prediction import PredictionOutcome

    outcome = PredictionOutcome(
        id=uuid.uuid4(),
        prediction_id=prediction_id,
        outcome_status=outcome_status,
        actual_price=actual_price,
        highest_price=highest_price,
        lowest_price=lowest_price,
        deviation_pct=deviation_pct,
        evaluated_at=datetime.now(UTC).replace(tzinfo=None),
        evaluation_date=evaluation_date or date(2026, 1, 15),
    )
    db_session.add(outcome)
    await db_session.flush()
    return outcome


async def create_test_watchlist_entry(
    db_session: AsyncSession,
    *,
    user_id: uuid.UUID,
    stock_id: uuid.UUID,
) -> "UserWatchlist":  # type: ignore[name-defined]  # noqa: F821
    from app.models.engagement import UserWatchlist

    entry = UserWatchlist(user_id=user_id, stock_id=stock_id)
    db_session.add(entry)
    await db_session.flush()
    return entry


async def create_test_follow_entry(
    db_session: AsyncSession,
    *,
    user_id: uuid.UUID,
    predictor_id: uuid.UUID,
) -> "UserFollowedPredictor":  # type: ignore[name-defined]  # noqa: F821
    from app.models.engagement import UserFollowedPredictor

    entry = UserFollowedPredictor(user_id=user_id, predictor_id=predictor_id)
    db_session.add(entry)
    await db_session.flush()
    return entry


async def create_test_notification(
    db_session: AsyncSession,
    *,
    user_id: uuid.UUID,
    type: str = "prediction_outcome",
    title: str = "Test notification",
    message: str | None = "Test message body",
    data: dict[str, str] | None = None,
    is_read: bool = False,
) -> "Notification":  # type: ignore[name-defined]  # noqa: F821
    from app.models.notification import Notification

    notification = Notification(
        id=uuid.uuid4(),
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        data=data or {},
        is_read=is_read,
    )
    db_session.add(notification)
    await db_session.flush()
    return notification


async def create_test_stock_daily_price(
    db_session: AsyncSession,
    *,
    stock_id: uuid.UUID,
    trade_date: date,
    close_price: Decimal = Decimal("1200.00"),
    open_price: Decimal | None = None,
    high_price: Decimal | None = None,
    low_price: Decimal | None = None,
    volume: int | None = None,
    adjusted_close: Decimal | None = None,
) -> "StockDailyPrice":  # type: ignore[name-defined]  # noqa: F821
    from app.models.stock import StockDailyPrice

    price = StockDailyPrice(
        id=uuid.uuid4(),
        stock_id=stock_id,
        trade_date=trade_date,
        open_price=open_price,
        high_price=high_price,
        low_price=low_price,
        close_price=close_price,
        volume=volume,
        adjusted_close=adjusted_close,
    )
    db_session.add(price)
    await db_session.flush()
    return price
