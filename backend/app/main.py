"""
PAIOS — Personal AI Operating System.

Application entry point.

Uses FastAPI lifespan for proper startup/shutdown lifecycle management.
All infrastructure is initialized through the Kernel, not here.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.kernel import boot, shutdown
from app.presentation.api.middleware.error_handler import register_error_handlers
from app.presentation.api.middleware.request_logging import RequestLoggingMiddleware
from app.presentation.api.middleware.rate_limit import RateLimitMiddleware
from app.presentation.api.middleware.security_headers import SecurityHeadersMiddleware
from app.presentation.api.v1.router import v1_router
from app.presentation.websocket.agent_monitor import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Application lifespan manager.

    Replaces the deprecated @app.on_event("startup") / @app.on_event("shutdown").
    """
    # ── Startup ────────────────────────────────────────────────────────
    await boot()
    yield
    # ── Shutdown ───────────────────────────────────────────────────────
    await shutdown()


def create_app() -> FastAPI:
    """
    Application factory.

    Creates and configures the FastAPI app with:
    - CORS middleware
    - Request logging middleware
    - Global error handlers
    - Versioned API routers
    """
    settings = get_settings()

    app = FastAPI(
        title=f"{settings.app_name} — Personal AI Operating System",
        description=(
            "Self-hosted, privacy-first AI Operating System that continuously "
            "works as your Digital Twin for career, learning, and growth."
        ),
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # ── Middleware (order matters: first added = outermost) ─────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware, rate_limit=100, period=60)
    app.add_middleware(RequestLoggingMiddleware)

    # ── Error Handlers ─────────────────────────────────────────────────
    register_error_handlers(app)

    # ── Routers ────────────────────────────────────────────────────────
    app.include_router(v1_router)
    app.include_router(ws_router)

    # ── Root ───────────────────────────────────────────────────────────
    @app.get("/", tags=["Root"])
    async def root() -> dict:
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "status": "operational",
            "docs": "/docs",
            "api": f"{settings.api_prefix}/system/health",
        }

    return app


# ── ASGI Application ──────────────────────────────────────────────────────
app = create_app()