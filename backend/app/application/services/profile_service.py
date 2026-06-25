"""
Profile Application Service.

Uses repository pattern and domain services for profile operations.
"""

from __future__ import annotations

from app.core.exceptions import EntityNotFoundError
from app.core.logging import get_logger
from app.domain.repositories.user_repository import UserRepository
from app.domain.services.profile_completion import (
    calculate_profile_completion,
    get_missing_sections,
)

logger = get_logger(__name__)


class ProfileService:
    """Profile read/update operations."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def get_profile(self, email: str) -> dict:
        """Get full profile (excluding password and resume_text)."""
        user = await self._user_repo.find_by_email(email)
        if user is None:
            raise EntityNotFoundError("User", email)
        return user.to_safe_dict()

    async def update_profile(self, email: str, data: dict) -> dict:
        """Update profile fields."""
        user = await self._user_repo.update_profile(email, data)
        if user is None:
            raise EntityNotFoundError("User", email)
        logger.info("profile_updated", email=email, fields=list(data.keys()))
        return user.to_safe_dict()

    async def get_summary(self, email: str) -> dict:
        """Get a summary of the user profile with completion score."""
        user = await self._user_repo.find_by_email(email)
        if user is None:
            raise EntityNotFoundError("User", email)

        user_dict = user.model_dump()
        completion = calculate_profile_completion(user_dict)
        missing = get_missing_sections(user_dict)

        return {
            "name": user.personal_details.full_name or user.full_name,
            "skills_count": len(user.skills),
            "projects_count": len(user.projects),
            "experience_count": len(user.experience),
            "certifications_count": len(user.certifications),
            "achievements_count": len(user.achievements),
            "profile_completion": completion,
            "missing_sections": missing,
        }
