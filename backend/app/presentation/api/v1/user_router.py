"""User Router — /api/v1/users endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, status, Response

from app.application.dependencies.auth import get_current_user
from app.application.dependencies.container import get_container
from app.application.schemas.user_schemas import UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Get the current authenticated user's profile."""
    container = get_container()
    user_data = await container.user_service.get_user(current_user["id"])
    return UserResponse(**user_data)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    body: UserUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Update the current authenticated user's profile details."""
    container = get_container()
    updated_data = await container.user_service.update_user(
        current_user["id"],
        body.model_dump(exclude_none=True),
    )
    return UserResponse(**updated_data)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Get a user by their unique ID (admin/owner only check)."""
    # Simple security rule: User can only access their own profile (or admin)
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("Not authorized to view this user profile")
    
    container = get_container()
    user_data = await container.user_service.get_user(user_id)
    return UserResponse(**user_data)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_by_id(
    user_id: str,
    body: UserUpdateRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> UserResponse:
    """Update a user's details by ID."""
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("Not authorized to update this user profile")

    container = get_container()
    updated_data = await container.user_service.update_user(
        user_id,
        body.model_dump(exclude_none=True),
    )
    return UserResponse(**updated_data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_by_id(
    user_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> Response:
    """Delete a user by ID."""
    if current_user["role"] != "admin" and current_user["id"] != user_id:
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("Not authorized to delete this user profile")

    container = get_container()
    await container.user_service.delete_user(user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
