from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.routes.admin import router as admin_router
from app.api.routes.auth import router as auth_router
from app.api.routes.extract import router as extract_router
from app.api.routes.following import router as following_router
from app.api.routes.health import router as health_router
from app.api.routes.notifications import router as notifications_router
from app.api.routes.outcomes import router as outcomes_router
from app.api.routes.predictions import router as predictions_router
from app.api.routes.predictors import router as predictors_router
from app.api.routes.search import router as search_router
from app.api.routes.stocks import router as stocks_router
from app.api.routes.watchlist import router as watchlist_router
from app.core.config import get_settings
from app.core.database import engine

settings = get_settings()

# Security headers per docs/SECURITY.md §8
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=(), payment=()",
    "Content-Security-Policy": (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self' " + " ".join(settings.cors_origins_list) + "; "
        "frame-ancestors 'none'"
    ),
}
if settings.ENVIRONMENT == "production":
    SECURITY_HEADERS["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        response = await call_next(request)
        for header, value in SECURITY_HEADERS.items():
            response.headers[header] = value
        return response


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

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(predictors_router, prefix="/api/v1")
app.include_router(stocks_router, prefix="/api/v1")
app.include_router(predictions_router, prefix="/api/v1")
app.include_router(extract_router, prefix="/api/v1")
app.include_router(outcomes_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(watchlist_router, prefix="/api/v1")
app.include_router(following_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")
