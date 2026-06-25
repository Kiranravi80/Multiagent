"""System Router — /api/v1/system endpoints for health and monitoring."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from app.application.dependencies.container import get_container
from app.core.config import get_settings

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health")
async def health_check() -> dict:
    """
    System health check.

    Returns the health status of all infrastructure components.
    """
    container = get_container()
    settings = get_settings()

    db_healthy = await container.db_manager.health_check()
    ai_healthy = await container.model_manager.health_check()

    checks = {
        "database": {"healthy": db_healthy, "type": "mongodb"},
        "ai_model": {
            "healthy": ai_healthy,
            "provider": "ollama",
            "default_model": settings.ollama_default_model,
        },
        "event_bus": {"healthy": True, "type": "in_memory"},
    }

    all_healthy = all(c["healthy"] for c in checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": checks,
    }


@router.get("/events/recent")
async def recent_events(limit: int = 50) -> dict:
    """Get recently published domain events (for monitoring)."""
    container = get_container()
    events = await container.event_bus.get_recent_events(limit=limit)
    return {
        "events": [e.to_dict() for e in events],
        "count": len(events),
    }


@router.get("/config")
async def get_config() -> dict:
    """Get non-sensitive configuration values."""
    settings = get_settings()
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "ollama_base_url": settings.ollama_base_url,
        "ollama_default_model": settings.ollama_default_model,
        "scheduler_enabled": settings.scheduler_enabled,
        "job_collection_interval_minutes": settings.job_collection_interval_minutes,
    }
