"""
PAIOS BaseAgent — Abstract Base Class for all AI Agents.

This is THE most important class in the entire system.
Every agent inherits from this and implements the required methods.

Provides:
- Lifecycle management (initialize, execute, pause, resume, shutdown)
- Event bus integration (publish, subscribe)
- State persistence (save_state, restore_state)
- Health monitoring
- Metrics collection
- Structured logging with agent context
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.core.constants import AgentStatus
from app.core.logging import get_logger
from app.domain.events.base import DomainEvent
from app.domain.models.agent_state import AgentStateModel
from app.infrastructure.event_bus.base import EventBus, EventHandler


@dataclass
class AgentResult:
    """Standard result from an agent execution."""

    success: bool
    data: dict[str, Any]
    message: str = ""
    errors: list[str] | None = None


@dataclass
class HealthStatus:
    """Health status report from an agent."""

    healthy: bool
    status: AgentStatus
    message: str = ""
    last_execution: datetime | None = None
    error_count: int = 0
    uptime_seconds: float = 0.0


class BaseAgent(ABC):
    """
    Abstract base class for all PAIOS AI agents.

    Every agent in the system (Career, Research, News, Learning, etc.)
    MUST inherit from this class and implement:
    - initialize(): Setup resources
    - execute(): Perform the agent's primary function
    - shutdown(): Clean up resources

    Lifecycle:
        1. __init__() → Agent created with dependencies
        2. initialize() → Resources allocated
        3. execute() → Called by orchestrator (possibly on schedule)
        4. pause()/resume() → Orchestrator manages workload
        5. shutdown() → Resources released

    Agents communicate ONLY through the EventBus:
        - publish_event() to send events
        - subscribe() to receive events
    """

    def __init__(
        self,
        *,
        name: str,
        event_bus: EventBus,
    ) -> None:
        self._name = name
        self._event_bus = event_bus
        self._status = AgentStatus.IDLE
        self._logger = get_logger(__name__, agent=name)
        self._state = AgentStateModel(agent_name=name)
        self._started_at: datetime | None = None

    # ── Properties ─────────────────────────────────────────────────────────

    @property
    def name(self) -> str:
        return self._name

    @property
    def status(self) -> AgentStatus:
        return self._status

    @property
    def state(self) -> AgentStateModel:
        return self._state

    # ── Abstract Methods (MUST implement) ──────────────────────────────────

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize agent resources.

        Called once when the agent is registered with the orchestrator.
        Use this for:
        - Subscribing to events
        - Loading configuration
        - Establishing connections
        """
        ...

    @abstractmethod
    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """
        Execute the agent's primary function.

        Called by the orchestrator, either on-demand or on a schedule.

        Args:
            context: Optional context data (e.g., specific job to process).

        Returns:
            AgentResult with success status and output data.
        """
        ...

    # ── Optional Overrides ─────────────────────────────────────────────────

    async def pause(self) -> None:
        """Pause agent execution. Override if agent has background work."""
        self._status = AgentStatus.PAUSED
        self._logger.info("agent_paused")

    async def resume(self) -> None:
        """Resume agent execution after a pause."""
        self._status = AgentStatus.RUNNING
        self._logger.info("agent_resumed")

    async def shutdown(self) -> None:
        """
        Clean up resources.

        Called when the system is shutting down.
        Override to close connections, save state, etc.
        """
        self._status = AgentStatus.STOPPED
        self._logger.info("agent_shutdown")

    # ── State Persistence ──────────────────────────────────────────────────

    async def save_state(self) -> dict[str, Any]:
        """
        Save agent state for crash recovery.

        Override to save custom state data.
        Returns a dict that can be passed to restore_state().
        """
        return self._state.model_dump()

    async def restore_state(self, state_data: dict[str, Any]) -> None:
        """
        Restore agent state after a crash or restart.

        Args:
            state_data: Dict from a previous save_state() call.
        """
        try:
            self._state = AgentStateModel.model_validate(state_data)
            self._logger.info("state_restored", agent=self._name)
        except Exception as exc:
            self._logger.warning("state_restore_failed", error=str(exc))

    # ── Health ─────────────────────────────────────────────────────────────

    async def health(self) -> HealthStatus:
        """Return the current health status of this agent."""
        uptime = 0.0
        if self._started_at:
            uptime = (datetime.now(UTC) - self._started_at).total_seconds()

        return HealthStatus(
            healthy=self._status not in (AgentStatus.ERROR, AgentStatus.STOPPED),
            status=self._status,
            message=self._state.last_error or "OK",
            last_execution=self._state.last_execution,
            error_count=self._state.error_count,
            uptime_seconds=uptime,
        )

    # ── Event Bus Integration ──────────────────────────────────────────────

    async def publish_event(self, event: DomainEvent) -> None:
        """Publish an event to the message bus."""
        await self._event_bus.publish(event)
        self._logger.debug("event_published", event_type=event.event_type)

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to events of a specific type."""
        await self._event_bus.subscribe(event_type, handler)
        self._logger.debug("event_subscribed", event_type=event_type)

    # ── Execution Wrapper ──────────────────────────────────────────────────

    async def run(self, context: dict[str, Any] | None = None) -> AgentResult:
        """
        Wrapper around execute() that handles lifecycle, metrics, and errors.

        Called by the orchestrator instead of execute() directly.
        """
        self._status = AgentStatus.RUNNING
        self._started_at = self._started_at or datetime.now(UTC)
        start_time = time.monotonic()

        self._logger.info("agent_execution_started")

        try:
            result = await self.execute(context)
            duration = time.monotonic() - start_time

            self._state.record_success(result=result.data, duration=duration)
            self._status = AgentStatus.IDLE

            self._logger.info(
                "agent_execution_completed",
                duration_s=round(duration, 2),
                success=result.success,
            )
            return result

        except Exception as exc:
            duration = time.monotonic() - start_time
            error_msg = str(exc)

            self._state.record_failure(error=error_msg)
            self._status = AgentStatus.ERROR

            self._logger.error(
                "agent_execution_failed",
                duration_s=round(duration, 2),
                error=error_msg,
                consecutive_errors=self._state.consecutive_errors,
            )

            return AgentResult(
                success=False,
                data={},
                message=f"Agent '{self._name}' failed: {error_msg}",
                errors=[error_msg],
            )
