"""Knowledge Router.

Provides endpoints to view tech digests, learning plans, arXiv papers, and GitHub trending repositories.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.application.dependencies.auth import get_current_user
from app.application.dependencies.container import get_container

router = APIRouter(prefix="/knowledge", tags=["Knowledge Intelligence"])


@router.get("/digests")
async def get_digests(
    digest_type: str | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Get all technical digests, optionally filtered by type."""
    container = get_container()
    filter_query = {}
    if digest_type:
        filter_query["type"] = digest_type

    digests = await container.digest_repo.find(filter_query)
    return {
        "digests": [d.model_dump() for d in digests],
        "count": len(digests)
    }


@router.get("/digests/latest")
async def get_latest_digest(
    digest_type: str = "daily",
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Fetch the most recent compiled technical digest."""
    container = get_container()
    digest = await container.digest_repo.get_latest_by_type(digest_type)
    if not digest:
        raise HTTPException(status_code=404, detail=f"No {digest_type} digests found.")
    return digest.model_dump()


@router.get("/learning-plans")
async def get_learning_plans(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Get the user's active learning plans and roadmaps."""
    container = get_container()
    
    # Query user
    users = await container.user_repo.get_all(limit=1)
    if not users:
        raise HTTPException(status_code=404, detail="No registered users found.")
    user = users[0]

    plans = await container.learning_plan_repo.get_by_user_id(user.id)
    return {
        "learning_plans": [p.model_dump() for p in plans],
        "count": len(plans)
    }


@router.get("/items")
async def get_knowledge_items(
    item_type: str | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Get tech knowledge entries (papers, repositories, startups, news)."""
    container = get_container()
    filter_query = {}
    if item_type:
        filter_query["type"] = item_type

    items = await container.knowledge_repo.find(filter_query)
    return {
        "items": [i.model_dump() for i in items],
        "count": len(items)
    }
