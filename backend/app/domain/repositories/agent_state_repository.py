"""Agent State Repository Interface.

Defines the contract for persisting and retrieving agent execution state and metrics.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.domain.models.agent_state import AgentStateModel
from app.domain.repositories.base import BaseRepository


class AgentStateRepository(BaseRepository[AgentStateModel], ABC):
    """Repository interface for Agent State."""

    @abstractmethod
    async def get_by_name(self, agent_name: str) -> AgentStateModel | None:
        """Retrieve agent state by its name.

        Args:
            agent_name: Name of the agent.

        Returns:
            The AgentStateModel if found, else None.
        """
        ...
