from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    echo=settings.ENVIRONMENT == "development",
)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Standalone session factory for use outside FastAPI request lifecycle (e.g. Celery tasks)
async_session_factory = async_session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session
