"""Interview Repository Interface.

Defines the contract for interview preparation sessions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from app.domain.models.interview import InterviewModel
from app.domain.repositories.base import BaseRepository


class InterviewRepository(BaseRepository[InterviewModel], ABC):
    """Repository interface for interview mock prep sessions."""

    @abstractmethod
    async def get_by_job_id(self, job_id: str) -> list[InterviewModel]:
        """Fetch all interview prep sessions mapped to a specific job ID."""
        ...
