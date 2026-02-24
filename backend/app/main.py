from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.admin import router as admin_router
from app.api.routes.health import router as health_router
from app.api.routes.predictions import router as predictions_router
from app.api.routes.predictors import router as predictors_router
from app.api.routes.stocks import router as stocks_router
from app.core.config import get_settings
from app.core.database import engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    yield
    await engine.dispose()


app = FastAPI(
    title="Enex API",
    description="Analyst Prediction Tracker for Indian Equity Markets",
    version=settings.APP_VERSION,
    docs_url="/docs",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(predictors_router, prefix="/api/v1")
app.include_router(stocks_router, prefix="/api/v1")
app.include_router(predictions_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
