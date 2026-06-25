"""Redis Event Bus.

Allows cross-process pub/sub event broadcasting.
"""

from __future__ import annotations

import asyncio
import json
from collections import defaultdict
from typing import Any
import redis.asyncio as aioredis

from app.core.logging import get_logger
from app.domain.events.base import DomainEvent
from app.infrastructure.event_bus.base import EventBus, EventHandler

logger = get_logger(__name__)

_MAX_RECENT_EVENTS = 500


class RedisEventBus(EventBus):
    """Redis-backed distributed Event Bus."""

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._redis: aioredis.Redis | None = None
        self._pubsub: aioredis.client.PubSub | None = None
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)
        self._recent_events: list[DomainEvent] = []
        self._lock = asyncio.Lock()
        self._listen_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        """Start the Redis connection and background listener."""
        if self._running:
            return

        self._redis = aioredis.from_url(self._redis_url, decode_responses=True)
        self._pubsub = self._redis.pubsub()
        self._running = True
        self._listen_task = asyncio.create_task(self._listen_loop())
        logger.info("redis_event_bus_started", url=self._redis_url)

    async def stop(self) -> None:
        """Stop the background listener and close connections."""
        self._running = False
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        if self._pubsub:
            await self._pubsub.close()
        if self._redis:
            await self._redis.close()
        logger.info("redis_event_bus_stopped")

    async def publish(self, event: DomainEvent) -> None:
        """Publish an event to a Redis channel named after the event type."""
        if not self._redis:
            await self.start()

        event_dict = event.to_dict()
        payload_str = json.dumps(event_dict)
        
        # Publish to Redis
        await self._redis.publish(event.event_type, payload_str)
        
        # Track locally for monitoring
        async with self._lock:
            self._recent_events.append(event)
            if len(self._recent_events) > _MAX_RECENT_EVENTS:
                self._recent_events = self._recent_events[-_MAX_RECENT_EVENTS:]

    async def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe local handler to event_type. Register channel on Redis pubsub."""
        if not self._redis:
            await self.start()

        first_subscriber = len(self._subscribers[event_type]) == 0
        self._subscribers[event_type].append(handler)
        
        if first_subscriber and self._pubsub:
            await self._pubsub.subscribe(event_type)
            logger.debug("redis_pubsub_subscribed", channel=event_type)

    async def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe handler. Unregister Redis channel if no subscribers left."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
            
        if len(self._subscribers[event_type]) == 0 and self._pubsub:
            await self._pubsub.unsubscribe(event_type)
            logger.debug("redis_pubsub_unsubscribed", channel=event_type)

    async def get_recent_events(self, *, limit: int = 50) -> list[DomainEvent]:
        async with self._lock:
            return list(reversed(self._recent_events[-limit:]))

    async def get_subscriber_count(self, event_type: str) -> int:
        return len(self._subscribers.get(event_type, []))

    async def _listen_loop(self) -> None:
        """Background loop reading from Redis pubsub and triggering handlers."""
        while self._running:
            try:
                if not self._pubsub:
                    await asyncio.sleep(0.5)
                    continue

                message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
                if message is None:
                    continue

                channel = message["channel"]
                data_str = message["data"]
                
                try:
                    data = json.loads(data_str)
                    event = DomainEvent.from_dict(data)
                except Exception as exc:
                    logger.error("redis_event_deserialization_failed", channel=channel, error=str(exc))
                    continue

                handlers = self._subscribers.get(channel, [])
                if handlers:
                    tasks = [self._safe_invoke(h, event) for h in handlers]
                    await asyncio.gather(*tasks)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("redis_event_bus_listen_loop_error", error=str(exc))
                await asyncio.sleep(1.0)

    @staticmethod
    async def _safe_invoke(handler: EventHandler, event: DomainEvent) -> None:
        try:
            await handler(event)
        except Exception as exc:
            logger.error(
                "redis_event_handler_failed",
                handler=handler.__qualname__,
                event_type=event.event_type,
                error=str(exc),
            )

    async def health_check(self) -> bool:
        """Ping Redis to check connection health."""
        if not self._redis:
            return False
        try:
            return await self._redis.ping()
        except Exception:
            return False
