"""
In-Memory Event Bus.

Lightweight event bus for development and single-node deployments.
All subscriptions and events are held in memory.

For production multi-node deployments, swap to RedisEventBus.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict

from app.core.logging import get_logger
from app.domain.events.base import DomainEvent
from app.infrastructure.event_bus.base import EventBus, EventHandler

logger = get_logger(__name__)

_MAX_RECENT_EVENTS = 500


class InMemoryEventBus(EventBus):
    """
    In-memory pub/sub event bus.

    Delivers events to all registered handlers asynchronously.
    Stores recent events for monitoring via the dashboard.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._recent_events: list[DomainEvent] = []
        self._lock = asyncio.Lock()

    async def publish(self, event: DomainEvent) -> None:
        """
        Publish an event to all subscribers.

        Handlers are invoked concurrently via asyncio.gather.
        Handler failures are logged but do not block other handlers.
        """
        logger.info(
            "event_published",
            event_type=event.event_type,
            source=event.source_agent,
            correlation_id=event.correlation_id,
        )

        # Store for monitoring
        async with self._lock:
            self._recent_events.append(event)
            if len(self._recent_events) > _MAX_RECENT_EVENTS:
                self._recent_events = self._recent_events[-_MAX_RECENT_EVENTS:]

        handlers = self._subscribers.get(event.event_type, [])

        if not handlers:
            logger.debug("event_no_subscribers", event_type=event.event_type)
            return

        # Invoke all handlers concurrently
        tasks = []
        for handler in handlers:
            tasks.append(self._safe_invoke(handler, event))

        await asyncio.gather(*tasks)

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._subscribers[event_type].append(handler)
        logger.debug(
            "event_subscribed",
            event_type=event_type,
            handler=handler.__qualname__,
        )

    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        handlers = self._subscribers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)
            logger.debug("event_unsubscribed", event_type=event_type)

    async def get_recent_events(self, *, limit: int = 50) -> list[DomainEvent]:
        return list(reversed(self._recent_events[-limit:]))

    async def get_subscriber_count(self, event_type: str) -> int:
        return len(self._subscribers.get(event_type, []))

    @staticmethod
    async def _safe_invoke(handler: EventHandler, event: DomainEvent) -> None:
        """Invoke a handler, catching and logging any errors."""
        try:
            await handler(event)
        except Exception as exc:
            logger.error(
                "event_handler_failed",
                handler=handler.__qualname__,
                event_type=event.event_type,
                error=str(exc),
            )

    @property
    def subscriber_map(self) -> dict[str, int]:
        """Return a summary of subscriber counts per event type."""
        return {
            event_type: len(handlers)
            for event_type, handlers in self._subscribers.items()
            if handlers
        }
