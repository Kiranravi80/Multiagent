"""Wellfound job collector stub."""

from __future__ import annotations

from app.core.logging import get_logger

logger = get_logger(__name__)


async def collect_wellfound_jobs() -> list[dict]:
    """Stub for collecting wellfound jobs."""
    logger.debug("collect_wellfound_jobs_stub_called")
    return []
