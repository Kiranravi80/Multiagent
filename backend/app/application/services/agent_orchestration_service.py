"""Agent Orchestration Service.

Wraps the MasterOrchestrator to expose orchestration features to the presentation layer.
"""

from __future__ import annotations

from typing import Any

from app.agents.base.agent import AgentResult
from app.agents.orchestrator.master_orchestrator import MasterOrchestrator


class AgentOrchestrationService:
    """Service to orchestrate agent operations."""

    def __init__(self, orchestrator: MasterOrchestrator) -> None:
        self._orchestrator = orchestrator

    async def get_system_status(self) -> dict[str, Any]:
        """Get the current system status and health of all agents."""
        return await self._orchestrator.get_system_status()

    async def execute_agent(
        self,
        agent_name: str,
        context: dict[str, Any] | None = None,
    ) -> AgentResult:
        """Manually trigger the execution of a specific agent."""
        return await self._orchestrator.execute_agent(agent_name, context=context)

    async def get_daily_summary(self) -> dict[str, Any]:
        """Get the daily summary statistics of agent executions."""
        return await self._orchestrator.get_daily_summary()
