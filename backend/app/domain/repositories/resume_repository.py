"""
Resume Repository Interface.
"""

from __future__ import annotations

from abc import abstractmethod

from app.core.constants import ResumeType
from app.domain.models.resume import ResumeModel
from app.domain.repositories.base import BaseRepository


class ResumeRepository(BaseRepository[ResumeModel]):
    """Abstract interface for resume data access."""

    @abstractmethod
    async def find_by_user(
        self,
        user_id: str,
        *,
        resume_type: ResumeType | None = None,
    ) -> list[ResumeModel]:
        """Find all resumes for a user, optionally filtered by type."""
        ...

    @abstractmethod
    async def find_latest_by_user(
        self,
        user_id: str,
        *,
        resume_type: ResumeType | None = None,
    ) -> ResumeModel | None:
        """Find the most recent resume for a user."""
        ...

    @abstractmethod
    async def find_by_job(self, job_id: str, user_id: str) -> ResumeModel | None:
        """Find a resume tailored for a specific job."""
        ...
