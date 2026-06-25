"""Learning Plan Repository Interface.

Defines the contract for persisting learning paths.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from app.domain.models.learning_plan import LearningPlanModel
from app.domain.repositories.base import BaseRepository


class LearningPlanRepository(BaseRepository[LearningPlanModel], ABC):
    """Repository interface for learning plans."""

    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> list[LearningPlanModel]:
        """Fetch all learning plans created for a user."""
        ...
