"""
User Repository Interface.

Extends BaseRepository with user-specific query methods.
"""

from __future__ import annotations

from abc import abstractmethod

from app.domain.models.user import UserModel
from app.domain.repositories.base import BaseRepository


class UserRepository(BaseRepository[UserModel]):
    """Abstract interface for user data access."""

    @abstractmethod
    async def find_by_email(self, email: str) -> UserModel | None:
        """Find a user by email address (unique field)."""
        ...

    @abstractmethod
    async def email_exists(self, email: str) -> bool:
        """Check if an email is already registered."""
        ...

    @abstractmethod
    async def update_profile(self, email: str, profile_data: dict) -> UserModel | None:
        """Update profile fields for a user identified by email."""
        ...

    @abstractmethod
    async def update_career_analysis(self, user_id: str, analysis: dict) -> bool:
        """Store AI-generated career analysis for a user."""
        ...

    @abstractmethod
    async def update_resume_data(
        self,
        user_id: str,
        *,
        resume_text: str = "",
        file_path: str = "",
        parsed_data: dict | None = None,
    ) -> bool:
        """Update resume-related fields for a user."""
        ...
