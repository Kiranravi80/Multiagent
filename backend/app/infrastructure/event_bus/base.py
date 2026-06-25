"""
Event Bus Abstract Interface.

Defines the contract for pub/sub message passing.
Implementations: InMemoryEventBus (dev), RedisEventBus (production).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from typing import Any

from app.domain.events.base import DomainEvent

# Type alias for async event handlers
EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


class EventBus(ABC):
    """
    Abstract pub/sub event bus.

    All agents communicate exclusively through this interface.
    Agents never call each other directly.
    """

    @abstractmethod
    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all subscribers of this event type.

        Args:
            event: The domain event to publish.
        """
        ...

    @abstractmethod
    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """
        Subscribe a handler to a specific event type.

        Args:
            event_type: The EventType string to subscribe to.
            handler: Async callable that processes the event.
        """
        ...

    @abstractmethod
    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a handler from an event type subscription."""
        ...

    @abstractmethod
    async def get_recent_events(self, *, limit: int = 50) -> list[DomainEvent]:
        """Return recently published events for monitoring."""
        ...

    @abstractmethod
    async def get_subscriber_count(self, event_type: str) -> int:
        """Return the number of handlers subscribed to an event type."""
        ...
