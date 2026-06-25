"""
Agent Registry.

Discovers, registers, and manages all AI agents in the system.
Used by the Master Orchestrator to track agent instances.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.logging import get_logger

if TYPE_CHECKING:
    from app.agents.base.agent import BaseAgent

logger = get_logger(__name__)


class AgentRegistry:
    """
    Central registry of all AI agents.

    Maintains a name → agent instance mapping.
    The orchestrator queries this to find, start, and monitor agents.
    """

    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        """
        Register an agent instance.

        Raises:
            ValueError: If an agent with this name is already registered.
        """
        if agent.name in self._agents:
            raise ValueError(f"Agent '{agent.name}' is already registered")

        self._agents[agent.name] = agent
        logger.info("agent_registered", agent=agent.name)

    def unregister(self, name: str) -> None:
        """Remove an agent from the registry."""
        if name in self._agents:
            del self._agents[name]
            logger.info("agent_unregistered", agent=name)

    def get(self, name: str) -> BaseAgent | None:
        """Get an agent by name."""
        return self._agents.get(name)

    def get_all(self) -> list[BaseAgent]:
        """Get all registered agents."""
        return list(self._agents.values())

    def get_names(self) -> list[str]:
        """Get all registered agent names."""
        return list(self._agents.keys())

    @property
    def count(self) -> int:
        return len(self._agents)

    def __contains__(self, name: str) -> bool:
        return name in self._agents
