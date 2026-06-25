"""
PAIOS Kernel — System Bootstrap and Lifecycle Manager.

The Kernel is responsible for:
1. Initializing logging
2. Booting the DI container (DB, AI, Event Bus)
3. Creating and registering all agents
4. Starting the scheduler
5. Managing graceful shutdown

This is the ONE place where the entire system is wired together.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.application.dependencies.container import get_container, initialize_container, shutdown_container
from app.domain.events.system_events import system_started_event, system_shutdown_event
from app.presentation.websocket.agent_monitor import register_ws_listener

logger = get_logger(__name__)


async def boot() -> None:
    """
    Boot the PAIOS system.

    Called once at application startup.
    Order matters — dependencies must be initialized first.
    """
    settings = get_settings()

    # 1. Initialize structured logging
    setup_logging(log_level=settings.log_level, log_format=settings.log_format)

    logger.info(
        "kernel_booting",
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
    )

    # 2. Initialize DI container (DB, AI, Event Bus, Orchestrator)
    container = await initialize_container()

    # Register WebSocket event listener
    await register_ws_listener()

    # 3. Publish system started event
    await container.event_bus.publish(
        system_started_event(
            version=settings.app_version,
            agents_loaded=container.orchestrator.registry.count,
        )
    )

    # 4. Start scheduler
    from app.schedulers.scheduler import start_scheduler
    start_scheduler()

    logger.info(
        "kernel_booted",
        agents_registered=container.orchestrator.registry.count,
        db_connected=container.db_manager.is_connected,
    )


async def shutdown() -> None:
    """
    Gracefully shut down the PAIOS system.

    Called once at application shutdown.
    Reverses the boot order.
    """
    logger.info("kernel_shutting_down")

    # Stop scheduler
    from app.schedulers.scheduler import stop_scheduler
    try:
        stop_scheduler()
    except Exception:
        pass

    try:
        container = get_container()
        await container.event_bus.publish(
            system_shutdown_event(reason="normal")
        )
    except Exception:
        pass

    await shutdown_container()

    logger.info("kernel_shutdown_complete")
