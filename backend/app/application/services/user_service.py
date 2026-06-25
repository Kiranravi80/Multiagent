"""
User Application Service.

CRUD operations via repository pattern.
"""

from __future__ import annotations

from app.core.exceptions import EntityNotFoundError
from app.core.logging import get_logger
from app.domain.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class UserService:
    """User CRUD operations."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def get_user(self, user_id: str) -> dict:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise EntityNotFoundError("User", user_id)
        return user.to_safe_dict()

    async def get_all_users(self, *, skip: int = 0, limit: int = 100) -> list[dict]:
        users = await self._user_repo.get_all(skip=skip, limit=limit)
        return [u.to_safe_dict() for u in users]

    async def update_user(self, user_id: str, data: dict) -> dict:
        user = await self._user_repo.update(user_id, data)
        if user is None:
            raise EntityNotFoundError("User", user_id)
        return user.to_safe_dict()

    async def delete_user(self, user_id: str) -> bool:
        deleted = await self._user_repo.delete(user_id)
        if not deleted:
            raise EntityNotFoundError("User", user_id)
        logger.info("user_deleted", user_id=user_id)
        return True
