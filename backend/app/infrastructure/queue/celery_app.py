"""Celery Task Queue Setup.

Initializes the Celery app instance for running asynchronous agents and tasks.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "paios",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Autodiscover tasks in the app.infrastructure.queue package
celery_app.autodiscover_tasks(["app.infrastructure.queue"])
