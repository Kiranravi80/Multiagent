"""Portfolio Repository Interface.

Defines the contract for user portfolio layout configurations.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from app.domain.models.portfolio import PortfolioModel
from app.domain.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository[PortfolioModel], ABC):
    """Repository interface for user portfolios."""

    @abstractmethod
    async def get_by_user_id(self, user_id: str) -> PortfolioModel | None:
        """Fetch the portfolio configuration of a specific user."""
        ...
