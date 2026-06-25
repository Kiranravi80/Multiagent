"""Application Repository Interface.

Defines the contract for job applications data access.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from app.domain.models.application import ApplicationModel
from app.domain.repositories.base import BaseRepository


class ApplicationRepository(BaseRepository[ApplicationModel], ABC):
    """Repository interface for Job Applications."""

    @abstractmethod
    async def get_by_user_and_job(self, user_id: str, job_id: str) -> ApplicationModel | None:
        """Find an application by user ID and job ID.

        Args:
            user_id: ID of the user.
            job_id: ID of the job.

        Returns:
            The ApplicationModel if found, else None.
        """
        ...
