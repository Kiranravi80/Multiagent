"""Application Router.

Provides endpoints to view, approve, and track job applications in the pipeline.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.application.dependencies.auth import get_current_user
from app.application.dependencies.container import get_container
from app.core.constants import ApplicationStatus, EventType
from app.domain.events.base import DomainEvent

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.get("")
async def get_applications(
    status: str | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Get all job applications with optional status filtering."""
    container = get_container()
    filter_query = {}
    if status:
        filter_query["status"] = status

    apps = await container.application_repo.find(filter_query)
    # Match with jobs info to make it richer
    enriched_apps = []
    for app in apps:
        app_dict = app.model_dump()
        job = await container.job_repo.get_by_id(app.job_id)
        if job:
            app_dict["job_title"] = job.title
            app_dict["company"] = job.company
            app_dict["location"] = job.location
            app_dict["source"] = job.source
        enriched_apps.append(app_dict)

    return {
        "applications": enriched_apps,
        "count": len(enriched_apps)
    }


@router.get("/{id}")
async def get_application(
    id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Get details of a single application."""
    container = get_container()
    app = await container.application_repo.get_by_id(id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    app_dict = app.model_dump()
    job = await container.job_repo.get_by_id(app.job_id)
    if job:
        app_dict["job"] = job.model_dump()
        
    return app_dict


@router.post("/{id}/approve")
async def approve_application(
    id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Approve a job application, triggering the ApplyAgent browser workflow."""
    container = get_container()
    app = await container.application_repo.get_by_id(id)
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Transition status
    app.transition_status(
        ApplicationStatus.APPROVED,
        notes=f"Approved by user {current_user.get('email')}"
    )
    await container.application_repo.update(app.id, app.model_dump(exclude={"id"}))

    # Publish APPLICATION_APPROVED event
    event = DomainEvent(
        event_type=EventType.APPLICATION_APPROVED,
        source_agent="user_router",
        payload={"application_id": app.id, "job_id": app.job_id}
    )
    await container.event_bus.publish(event)

    return {
        "success": True,
        "message": "Application approved. Automating submission via browser.",
        "status": app.status
    }
