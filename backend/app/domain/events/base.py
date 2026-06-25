"""
PAIOS Domain Event Base.

Every event in the PAIOS message bus is a frozen dataclass.
Events are immutable facts — something that already happened.

All agents communicate exclusively through events published on the EventBus.
Agents never call each other directly.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass(frozen=True)
class DomainEvent:
    """
    Base class for all domain events in the PAIOS Message Bus.

    Attributes:
        event_id: Unique identifier for this event instance.
        event_type: The event type string (from EventType enum).
        timestamp: When the event occurred (UTC).
        source_agent: Name of the agent/service that produced this event.
        payload: Arbitrary event-specific data.
        correlation_id: Links related events in a processing chain.
                        For example, a JOB_COLLECTED event and its
                        downstream JOB_CLASSIFIED event share the same
                        correlation_id.
        metadata: Optional additional context (request_id, user_id, etc.).
    """

    event_type: str
    source_agent: str
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict for storage or transport."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "source_agent": self.source_agent,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DomainEvent:
        """Deserialize from a plain dict."""
        ts = data.get("timestamp")
        if isinstance(ts, str):
            ts = datetime.fromisoformat(ts)
        elif ts is None:
            ts = datetime.now(UTC)

        return cls(
            event_id=data.get("event_id", uuid.uuid4().hex),
            event_type=data["event_type"],
            timestamp=ts,
            source_agent=data.get("source_agent", "unknown"),
            payload=data.get("payload", {}),
            correlation_id=data.get("correlation_id", uuid.uuid4().hex),
            metadata=data.get("metadata", {}),
        )
