"""Remotive job collector stub."""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


async def collect_remotive_jobs() -> list[dict]:
    """Stub for collecting remotive jobs."""
    logger.debug("collect_remotive_jobs_stub_called")
    return []
