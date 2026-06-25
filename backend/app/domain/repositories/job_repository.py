"""
Job Repository Interface.

Extends BaseRepository with job-specific query methods
for the career pipeline.
"""

from __future__ import annotations

from abc import abstractmethod

from app.core.constants import JobSource, JobStatus
from app.domain.models.job import JobModel
from app.domain.repositories.base import BaseRepository


class JobRepository(BaseRepository[JobModel]):
    """Abstract interface for job data access."""

    @abstractmethod
    async def find_by_fingerprint(self, fingerprint: str) -> JobModel | None:
        """Find a job by its dedup fingerprint."""
        ...

    @abstractmethod
    async def fingerprint_exists(self, fingerprint: str) -> bool:
        """Check if a job with this fingerprint already exists."""
        ...

    @abstractmethod
    async def find_by_source(
        self,
        source: JobSource,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobModel]:
        """Find jobs from a specific source platform."""
        ...

    @abstractmethod
    async def find_by_status(
        self,
        status: JobStatus,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobModel]:
        """Find jobs at a specific pipeline stage."""
        ...

    @abstractmethod
    async def update_status(self, job_id: str, status: JobStatus) -> bool:
        """Update the pipeline status of a job."""
        ...

    @abstractmethod
    async def update_classification(self, job_id: str, classification: dict) -> bool:
        """Store classification results for a job."""
        ...

    @abstractmethod
    async def update_jd_analysis(self, job_id: str, analysis: dict) -> bool:
        """Store JD analysis results for a job."""
        ...

    @abstractmethod
    async def bulk_create(self, jobs: list[JobModel]) -> int:
        """
        Insert multiple jobs, skipping duplicates (by fingerprint).

        Returns:
            Number of new jobs actually inserted.
        """
        ...
