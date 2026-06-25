"""
Master Orchestrator.

The brain of PAIOS — manages all agent lifecycles, scheduling,
failure recovery, and system health.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from typing import Any

from app.agents.base.agent import AgentResult, BaseAgent, HealthStatus
from app.agents.base.agent_registry import AgentRegistry
from app.core.constants import AgentStatus
from app.core.logging import get_logger
from app.domain.events.base import DomainEvent
from app.domain.events.system_events import (
    agent_error_event,
    agent_registered_event,
    agent_started_event,
)
from app.infrastructure.event_bus.base import EventBus

logger = get_logger(__name__)

# Max consecutive failures before the orchestrator stops retrying
_MAX_CONSECUTIVE_FAILURES = 5


class MasterOrchestrator:
    """
    The Master Orchestrator — the brain of PAIOS.

    Responsibilities:
    - Register and initialize all agents
    - Execute agents on demand or schedule
    - Restart failed agents with exponential backoff
    - Collect health metrics from all agents
    - Generate execution summaries
    - Store execution history
    """

    def __init__(self, *, event_bus: EventBus) -> None:
        self._event_bus = event_bus
        self._registry = AgentRegistry()
        self._execution_history: list[dict[str, Any]] = []
        self._started_at: datetime | None = None

    # ── Agent Management ───────────────────────────────────────────────────

    async def register_agent(self, agent: BaseAgent) -> None:
        """Register, restore state, and initialize an agent."""
        self._registry.register(agent)

        try:
            # Restore state from database
            try:
                from app.application.dependencies.container import get_container
                state_repo = get_container().agent_state_repo
                persisted_state = await state_repo.get_by_name(agent.name)
                if persisted_state:
                    await agent.restore_state(persisted_state.model_dump())
                    logger.info("orchestrator_agent_state_restored", agent=agent.name)
            except Exception as exc:
                logger.warning("orchestrator_agent_state_restore_failed", agent=agent.name, error=str(exc))

            await agent.initialize()
            await self._event_bus.publish(
                agent_registered_event(agent_name=agent.name)
            )
            logger.info("orchestrator_agent_registered", agent=agent.name)
        except Exception as exc:
            logger.error(
                "orchestrator_agent_init_failed",
                agent=agent.name,
                error=str(exc),
            )

    async def execute_agent(
        self,
        agent_name: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> AgentResult:
        """
        Execute a specific agent with retries and persist state.

        Uses the BaseAgent.run() wrapper which handles metrics and errors.
        """
        agent = self._registry.get(agent_name)
        if agent is None:
            return AgentResult(
                success=False,
                data={},
                message=f"Agent '{agent_name}' not found",
                errors=[f"Unknown agent: {agent_name}"],
            )

        # Don't run if already running
        if agent.status == AgentStatus.RUNNING:
            return AgentResult(
                success=False,
                data={},
                message=f"Agent '{agent_name}' is already running",
            )

        await self._event_bus.publish(
            agent_started_event(agent_name=agent_name)
        )

        # Retry Engine configuration parameters from agent properties or defaults
        max_retries = getattr(agent, "max_retries", 2)
        strategy = getattr(agent, "retry_strategy", "exponential_backoff_with_jitter")

        from app.core.retry import RetryEngine

        async def _run_attempt() -> AgentResult:
            res = await agent.run(context)
            if not res.success:
                raise RuntimeError(res.message or "Agent run failed")
            return res

        try:
            if max_retries > 0:
                result = await RetryEngine.retry_async(
                    _run_attempt,
                    max_retries=max_retries,
                    strategy=strategy,
                    operation_name=f"agent_run_{agent_name}",
                )
            else:
                result = await agent.run(context)
        except Exception as exc:
            # All retry attempts failed, returning the final status
            result = AgentResult(
                success=False,
                data={},
                message=f"Agent '{agent_name}' execution failed after retries: {exc}",
                errors=[str(exc)],
            )

        # Persist state after run
        try:
            from app.application.dependencies.container import get_container
            state_repo = get_container().agent_state_repo
            state_data = await agent.save_state()
            db_state = await state_repo.get_by_name(agent.name)
            if db_state:
                await state_repo.update(db_state.id, state_data)
            else:
                from app.domain.models.agent_state import AgentStateModel
                model = AgentStateModel.model_validate(state_data)
                await state_repo.create(model)
            logger.info("orchestrator_agent_state_saved", agent=agent_name)
        except Exception as exc:
            logger.error("orchestrator_save_state_failed", agent=agent_name, error=str(exc))

        # Record in history
        self._execution_history.append({
            "agent": agent_name,
            "timestamp": datetime.now(UTC).isoformat(),
            "success": result.success,
            "message": result.message,
        })

        # Trim history
        if len(self._execution_history) > 1000:
            self._execution_history = self._execution_history[-1000:]

        # Handle failure
        if not result.success and agent.state.consecutive_errors >= _MAX_CONSECUTIVE_FAILURES:
            logger.error(
                "agent_max_failures_reached",
                agent=agent_name,
                consecutive_errors=agent.state.consecutive_errors,
            )
            await self._event_bus.publish(
                agent_error_event(
                    agent_name=agent_name,
                    error=f"Max consecutive failures ({_MAX_CONSECUTIVE_FAILURES}) reached",
                )
            )

        return result

    async def execute_all(self) -> dict[str, AgentResult]:
        """Execute all registered agents sequentially."""
        results: dict[str, AgentResult] = {}
        for agent in self._registry.get_all():
            results[agent.name] = await self.execute_agent(agent.name)
        return results

    # ── Health & Monitoring ────────────────────────────────────────────────

    async def get_all_health(self) -> dict[str, dict[str, Any]]:
        """Get health status of all registered agents."""
        health_map: dict[str, dict[str, Any]] = {}

        for agent in self._registry.get_all():
            try:
                h = await agent.health()
                health_map[agent.name] = {
                    "healthy": h.healthy,
                    "status": h.status.value,
                    "message": h.message,
                    "last_execution": h.last_execution.isoformat() if h.last_execution else None,
                    "error_count": h.error_count,
                    "uptime_seconds": round(h.uptime_seconds, 1),
                }
            except Exception as exc:
                health_map[agent.name] = {
                    "healthy": False,
                    "status": "error",
                    "message": str(exc),
                }

        return health_map

    async def get_system_status(self) -> dict[str, Any]:
        """Get overall system status summary."""
        agents_health = await self.get_all_health()

        total = len(agents_health)
        healthy = sum(1 for h in agents_health.values() if h.get("healthy"))

        return {
            "status": "healthy" if healthy == total else "degraded" if healthy > 0 else "unhealthy",
            "agents_total": total,
            "agents_healthy": healthy,
            "agents_unhealthy": total - healthy,
            "agents": agents_health,
            "started_at": self._started_at.isoformat() if self._started_at else None,
            "recent_executions": self._execution_history[-20:],
        }

    async def get_daily_summary(self) -> dict[str, Any]:
        """Generate a daily execution summary."""
        today = datetime.now(UTC).date().isoformat()

        today_executions = [
            e for e in self._execution_history
            if e["timestamp"].startswith(today)
        ]

        successes = sum(1 for e in today_executions if e["success"])
        failures = len(today_executions) - successes

        return {
            "date": today,
            "total_executions": len(today_executions),
            "successes": successes,
            "failures": failures,
            "success_rate": round(successes / max(len(today_executions), 1) * 100, 1),
            "agents_executed": list({e["agent"] for e in today_executions}),
        }

    # ── Lifecycle ──────────────────────────────────────────────────────────

    async def start(self) -> None:
        """Start the orchestrator."""
        self._started_at = datetime.now(UTC)
        logger.info("orchestrator_started", agents=self._registry.count)

    async def shutdown(self) -> None:
        """Gracefully shut down all agents."""
        logger.info("orchestrator_shutting_down")

        for agent in self._registry.get_all():
            try:
                await agent.shutdown()
            except Exception as exc:
                logger.error("agent_shutdown_failed", agent=agent.name, error=str(exc))

        logger.info("orchestrator_shutdown_complete")

    @property
    def registry(self) -> AgentRegistry:
        return self._registry
