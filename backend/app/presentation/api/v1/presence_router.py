"""Presence Router.

Provides endpoints to view/approve drafted posts, layout settings, and target network contacts.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.application.dependencies.auth import get_current_user
from app.application.dependencies.container import get_container
from app.core.constants import EventType
from app.domain.events.base import DomainEvent
from app.domain.models.portfolio import PortfolioModel

router = APIRouter(prefix="/presence", tags=["Professional Presence"])


@router.get("/content")
async def get_content(
    status: str | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Get technical content drafts filtered by status."""
    container = get_container()
    filter_query = {}
    if status:
        filter_query["status"] = status

    contents = await container.content_repo.find(filter_query)
    return {
        "contents": [c.model_dump() for c in contents],
        "count": len(contents)
    }


@router.post("/content/{id}/approve")
async def approve_content(
    id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Approve a draft content item, transitioning status to approved/published."""
    container = get_container()
    content = await container.content_repo.get_by_id(id)
    if not content:
        raise HTTPException(status_code=404, detail="Content not found")

    content.status = "approved"
    content.approved_at = datetime.now(UTC)
    await container.content_repo.update(content.id, content.to_dict())

    # Publish CONTENT_APPROVED event
    event = DomainEvent(
        event_type=EventType.CONTENT_APPROVED,
        source_agent="presence_router",
        payload={"content_id": content.id, "platform": content.platform}
    )
    await container.event_bus.publish(event)

    return {
        "success": True,
        "message": "Content draft approved successfully.",
        "status": content.status
    }


@router.get("/portfolio")
async def get_portfolio(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Get the user's active portfolio layout configuration."""
    container = get_container()
    
    users = await container.user_repo.get_all(limit=1)
    if not users:
        raise HTTPException(status_code=404, detail="No registered users found.")
    user = users[0]

    portfolio = await container.portfolio_repo.get_by_user_id(user.id)
    if not portfolio:
        raise HTTPException(status_code=404, detail="Portfolio config not found.")
    return portfolio.model_dump()


@router.post("/portfolio")
async def update_portfolio(
    bio: str,
    skills: list[str],
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Update layout bio/skills details manually."""
    container = get_container()
    
    users = await container.user_repo.get_all(limit=1)
    if not users:
        raise HTTPException(status_code=404, detail="No registered users found.")
    user = users[0]

    portfolio = await container.portfolio_repo.get_by_user_id(user.id)
    if portfolio:
        portfolio.bio = bio
        portfolio.skills = skills
        portfolio.updated_at = datetime.now(UTC)
        await container.portfolio_repo.update(portfolio.id, portfolio.to_dict())
        portfolio_id = portfolio.id
    else:
        new_portfolio = PortfolioModel(
            user_id=user.id,
            bio=bio,
            skills=skills,
            projects=[],
            socials={},
            layout={}
        )
        portfolio_id = await container.portfolio_repo.create(new_portfolio)

    return {
        "success": True,
        "portfolio_id": portfolio_id,
        "message": "Portfolio config updated successfully."
    }


@router.get("/networking")
async def get_networking(
    status: str | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Get identified network contacts/leads."""
    container = get_container()
    filter_query = {}
    if status:
        filter_query["status"] = status

    contacts = await container.networking_repo.find(filter_query)
    return {
        "contacts": [c.model_dump() for c in contacts],
        "count": len(contacts)
    }
