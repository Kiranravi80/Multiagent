"""
System Domain Events.

Events related to the PAIOS kernel, agent lifecycle, and health monitoring.
"""

from __future__ import annotations

from typing import Any

from app.core.constants import EventType
from app.domain.events.base import DomainEvent


def system_started_event(*, version: str, agents_loaded: int) -> DomainEvent:
    return DomainEvent(
        event_type=EventType.SYSTEM_STARTED,
        source_agent="kernel",
        payload={"version": version, "agents_loaded": agents_loaded},
    )


def system_shutdown_event(*, reason: str = "normal") -> DomainEvent:
    return DomainEvent(
        event_type=EventType.SYSTEM_SHUTDOWN,
        source_agent="kernel",
        payload={"reason": reason},
    )


def agent_registered_event(*, agent_name: str) -> DomainEvent:
    return DomainEvent(
        event_type=EventType.AGENT_REGISTERED,
        source_agent="orchestrator",
        payload={"agent_name": agent_name},
    )


def agent_started_event(*, agent_name: str) -> DomainEvent:
    return DomainEvent(
        event_type=EventType.AGENT_STARTED,
        source_agent="orchestrator",
        payload={"agent_name": agent_name},
    )


def agent_stopped_event(*, agent_name: str, reason: str = "normal") -> DomainEvent:
    return DomainEvent(
        event_type=EventType.AGENT_STOPPED,
        source_agent="orchestrator",
        payload={"agent_name": agent_name, "reason": reason},
    )


def agent_error_event(
    *, agent_name: str, error: str, details: dict[str, Any] | None = None
) -> DomainEvent:
    return DomainEvent(
        event_type=EventType.AGENT_ERROR,
        source_agent="orchestrator",
        payload={
            "agent_name": agent_name,
            "error": error,
            "details": details or {},
        },
    )


def health_check_event(
    *, source: str, status: str, checks: dict[str, Any]
) -> DomainEvent:
    return DomainEvent(
        event_type=EventType.HEALTH_CHECK,
        source_agent=source,
        payload={"status": status, "checks": checks},
    )
