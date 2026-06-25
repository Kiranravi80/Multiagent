"""PAIOS System Scheduler.

APScheduler orchestrates agent execution intervals, enqueuing background Celery tasks.
"""

from __future__ import annotations

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.core.config import get_settings
from app.core.logging import get_logger
from app.infrastructure.queue.tasks import run_agent_task

logger = get_logger(__name__)

scheduler = AsyncIOScheduler()


def trigger_agent_execution(agent_name: str) -> None:
    """Trigger agent execution by enqueuing a Celery background task."""
    logger.info("scheduler_triggering_agent_task", agent=agent_name)
    run_agent_task.delay(agent_name)


def start_scheduler() -> None:
    """Bootstrap scheduler jobs based on configured settings."""
    settings = get_settings()
    if not settings.scheduler_enabled:
        logger.info("scheduler_disabled_by_config")
        return

    # Trigger job collection sequence via career_agent
    scheduler.add_job(
        trigger_agent_execution,
        "interval",
        args=["career_agent"],
        minutes=settings.job_collection_interval_minutes,
        id="job_collection_run",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        "scheduler_started",
        interval_minutes=settings.job_collection_interval_minutes,
    )


def stop_scheduler() -> None:
    """Stop the scheduler instance."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("scheduler_stopped")