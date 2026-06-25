"""Communication Router.

Provides endpoints to view/manage email correspondence queues and calendar holdings.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.application.dependencies.auth import get_current_user
from app.application.dependencies.container import get_container
from app.core.constants import EventType
from app.domain.events.base import DomainEvent

router = APIRouter(prefix="/communication", tags=["Communication & Scheduling"])


@router.get("/emails")
async def get_emails(
    status: str | None = None,
    email_type: str | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Get list of email correspondence log items."""
    container = get_container()
    filter_query = {}
    if status:
        filter_query["status"] = status
    if email_type:
        filter_query["type"] = email_type

    emails = await container.email_repo.find(filter_query)
    return {
        "emails": [e.model_dump() for e in emails],
        "count": len(emails)
    }


@router.post("/emails/{id}/send")
async def send_email_draft(
    id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Approve a draft outbound email, simulating the SMTP send action and updating status."""
    container = get_container()
    email = await container.email_repo.get_by_id(id)
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")

    if email.status != "draft" and email.status != "pending_approval":
        raise HTTPException(status_code=400, detail="Only drafts or pending emails can be sent manually.")

    # Update status to sent
    email.status = "sent"
    email.sent_at = datetime.now(UTC)
    await container.email_repo.update(email.id, email.to_dict())

    # Publish EMAIL_SENT event
    event = DomainEvent(
        event_type=EventType.EMAIL_SENT,
        source_agent="communication_router",
        payload={
            "email_id": email.id,
            "to_email": email.to_email,
            "subject": email.subject
        }
    )
    await container.event_bus.publish(event)

    return {
        "success": True,
        "message": f"Email successfully dispatched to {email.to_email}.",
        "status": email.status
    }


@router.get("/calendar")
async def get_calendar(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Get all scheduled holds and interviews."""
    container = get_container()
    events = await container.calendar_repo.get_all()
    return {
        "events": [ev.model_dump() for ev in events],
        "count": len(events)
    }
