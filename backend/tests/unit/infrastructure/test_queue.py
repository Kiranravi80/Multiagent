from app.infrastructure.queue.celery_app import celery_app
from app.infrastructure.queue import tasks as _tasks


def test_celery_tasks_registered() -> None:
    """Verify Celery registers the PAIOS agent execution task."""
    registered_tasks = list(celery_app.tasks.keys())
    assert "app.tasks.run_agent" in registered_tasks
