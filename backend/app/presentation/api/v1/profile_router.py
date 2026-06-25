"""Profile Router — /api/v1/profile endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.application.dependencies.auth import get_current_user
from app.application.dependencies.container import get_container
from app.application.schemas.profile_schemas import (
    ProfileSummaryResponse,
    ProfileUpdateRequest,
)

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("/me")
async def get_my_profile(current_user: dict[str, Any] = Depends(get_current_user)) -> dict:
    container = get_container()
    return await container.profile_service.get_profile(current_user["email"])


@router.put("/me")
async def update_my_profile(
    body: ProfileUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    container = get_container()
    return await container.profile_service.update_profile(
        current_user["email"],
        body.model_dump(exclude_none=True),
    )


@router.get("/summary", response_model=ProfileSummaryResponse)
async def profile_summary(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> ProfileSummaryResponse:
    container = get_container()
    data = await container.profile_service.get_summary(current_user["email"])
    return ProfileSummaryResponse(**data)
