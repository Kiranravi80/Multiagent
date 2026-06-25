"""Celery background tasks definitions."""

from __future__ import annotations

import asyncio
from typing import Any

from app.application.dependencies.container import get_container
from app.core.logging import get_logger
from app.infrastructure.queue.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.run_agent")
def run_agent_task(agent_name: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute an agent asynchronously in the Celery worker process."""
    logger.info("celery_run_agent_task_started", agent=agent_name)

    # Resolve event loop for run_until_complete
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    async def _execute() -> dict[str, Any]:
        container = get_container()
        # Initialize container connection (MongoDB, models, etc.)
        await container.initialize()

        try:
            result = await container.agent_orchestration_service.execute_agent(
                agent_name, context=context
            )
            return {
                "success": result.success,
                "agent_name": agent_name,
                "message": result.message,
                "data": result.data,
                "errors": result.errors,
            }
        finally:
            await container.shutdown()

    try:
        res = loop.run_until_complete(_execute())
        logger.info("celery_run_agent_task_completed", agent=agent_name, success=res["success"])
        return res
    except Exception as exc:
        logger.error("celery_run_agent_task_failed", agent=agent_name, error=str(exc))
        return {
            "success": False,
            "agent_name": agent_name,
            "message": f"Task execution failed: {exc}",
            "errors": [str(exc)],
        }
