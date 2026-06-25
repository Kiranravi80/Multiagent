"""
Agent State Domain Model.

Tracks the runtime state, metrics, and execution history of each AI agent.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import AgentStatus


class AgentMetrics(BaseModel):
    """Execution metrics for an agent."""

    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_duration_seconds: float = 0.0
    last_duration_seconds: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions * 100


class AgentStateModel(BaseModel):
    """
    Persistent state of an AI agent.

    Used by save_state/restore_state for crash recovery and by the
    dashboard for real-time agent monitoring.
    """

    id: str = ""
    agent_name: str
    status: AgentStatus = AgentStatus.IDLE

    last_execution: datetime | None = None
    last_result: dict[str, Any] = Field(default_factory=dict)
    last_error: str | None = None

    error_count: int = 0
    consecutive_errors: int = 0

    state_data: dict[str, Any] = Field(default_factory=dict)
    metrics: AgentMetrics = Field(default_factory=AgentMetrics)

    registered_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def record_success(self, *, result: dict[str, Any], duration: float) -> None:
        """Record a successful execution."""
        self.last_execution = datetime.now(UTC)
        self.last_result = result
        self.last_error = None
        self.consecutive_errors = 0
        self.status = AgentStatus.IDLE
        self.updated_at = datetime.now(UTC)

        self.metrics.total_executions += 1
        self.metrics.successful_executions += 1
        self.metrics.last_duration_seconds = duration

        # Running average
        n = self.metrics.total_executions
        prev_avg = self.metrics.avg_duration_seconds
        self.metrics.avg_duration_seconds = prev_avg + (duration - prev_avg) / n

    def record_failure(self, *, error: str) -> None:
        """Record a failed execution."""
        self.last_execution = datetime.now(UTC)
        self.last_error = error
        self.error_count += 1
        self.consecutive_errors += 1
        self.status = AgentStatus.ERROR
        self.updated_at = datetime.now(UTC)

        self.metrics.total_executions += 1
        self.metrics.failed_executions += 1
