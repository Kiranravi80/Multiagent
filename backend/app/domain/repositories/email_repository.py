"""Email Repository Interface.

Defines the contract for email logs and draft queue operations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from app.domain.models.email import EmailModel
from app.domain.repositories.base import BaseRepository


class EmailRepository(BaseRepository[EmailModel], ABC):
    """Repository interface for email correspondence."""

    @abstractmethod
    async def get_by_thread_id(self, thread_id: str) -> list[EmailModel]:
        """Fetch all email items sharing a specific thread ID."""
        ...
