import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.domain.events.base import DomainEvent
from app.infrastructure.event_bus.in_memory_bus import InMemoryEventBus
from app.infrastructure.event_bus.redis_bus import RedisEventBus


@pytest.mark.asyncio
async def test_in_memory_event_bus() -> None:
    bus = InMemoryEventBus()
    received_events = []

    async def handler(event: DomainEvent) -> None:
        received_events.append(event)

    await bus.subscribe("TEST_EVENT", handler)
    assert await bus.get_subscriber_count("TEST_EVENT") == 1

    event = DomainEvent(
        event_type="TEST_EVENT",
        source_agent="test_agent",
        payload={"val": 42},
    )
    await bus.publish(event)

    # Let the async tasks run
    await asyncio.sleep(0.01)
    assert len(received_events) == 1
    assert received_events[0].payload["val"] == 42


@pytest.mark.asyncio
async def test_redis_event_bus_mocked() -> None:
    with patch("redis.asyncio.from_url") as mock_from_url:
        mock_redis = MagicMock()
        mock_pubsub = AsyncMock()
        mock_redis.pubsub.return_value = mock_pubsub
        mock_from_url.return_value = mock_redis

        bus = RedisEventBus(redis_url="redis://localhost:6379/0")
        await bus.start()
        assert bus._running is True

        event = DomainEvent(
            event_type="TEST_EVENT",
            source_agent="test_agent",
            payload={"x": 100},
        )
        await bus.publish(event)
        mock_redis.publish.assert_called_once()

        await bus.stop()
        assert bus._running is False
