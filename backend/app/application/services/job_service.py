"""
Job Application Service.

Orchestrates job collection, listing, and pipeline operations.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.domain.repositories.job_repository import JobRepository

logger = get_logger(__name__)


class JobService:
    """Job listing and pipeline operations."""

    def __init__(self, job_repo: JobRepository) -> None:
        self._job_repo = job_repo

    async def get_jobs(
        self,
        *,
        skip: int = 0,
        limit: int = 50,
        status: str | None = None,
        source: str | None = None,
    ) -> dict[str, Any]:
        """Get paginated job listings with optional filters."""
        filter_query: dict[str, Any] = {}
        if status:
            filter_query["status"] = status
        if source:
            filter_query["source"] = source

        if filter_query:
            jobs = await self._job_repo.find(filter_query, skip=skip, limit=limit)
        else:
            jobs = await self._job_repo.get_all(skip=skip, limit=limit)

        total = await self._job_repo.count(filter_query or None)

        return {
            "jobs": [j.model_dump() for j in jobs],
            "total": total,
            "skip": skip,
            "limit": limit,
            "has_more": (skip + limit) < total,
        }

    async def get_job(self, job_id: str) -> dict[str, Any] | None:
        """Get a single job by ID."""
        job = await self._job_repo.get_by_id(job_id)
        if job is None:
            return None
        return job.model_dump()

    async def get_stats(self) -> dict[str, Any]:
        """Get job collection statistics."""
        total = await self._job_repo.count()
        new = await self._job_repo.count({"status": "new"})
        classified = await self._job_repo.count({"status": "classified"})
        analyzed = await self._job_repo.count({"status": "analyzed"})
        matched = await self._job_repo.count({"status": "matched"})

        return {
            "total": total,
            "new": new,
            "classified": classified,
            "analyzed": analyzed,
            "matched": matched,
        }
