"""Knowledge Repository Interface.

Defines the contract for technical articles, repositories, and news.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from app.domain.models.knowledge import KnowledgeModel
from app.domain.repositories.base import BaseRepository


class KnowledgeRepository(BaseRepository[KnowledgeModel], ABC):
    """Repository interface for technical knowledge elements."""

    @abstractmethod
    async def get_by_type(self, item_type: str, *, skip: int = 0, limit: int = 50) -> list[KnowledgeModel]:
        """Fetch knowledge items by their classification type."""
        ...
