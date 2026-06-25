"""
Auth Application Service.

Migrated from app/services/auth_service.py.
Now uses repository pattern and typed exceptions instead of returning None.
"""

from __future__ import annotations

from app.core.exceptions import AuthenticationError, DuplicateEntityError
from app.core.logging import get_logger
from app.core.security import create_access_token, hash_password, verify_password
from app.domain.models.user import UserModel
from app.domain.repositories.user_repository import UserRepository

logger = get_logger(__name__)


class AuthService:
    """Handles user registration and authentication."""

    def __init__(self, user_repo: UserRepository) -> None:
        self._user_repo = user_repo

    async def register(self, *, full_name: str, email: str, password: str) -> str:
        """
        Register a new user.

        Returns:
            The new user's ID.

        Raises:
            DuplicateEntityError: If email already exists.
        """
        if await self._user_repo.email_exists(email):
            raise DuplicateEntityError("User", field="email", value=email)

        user = UserModel(
            email=email,
            password=hash_password(password),
            full_name=full_name,
        )
        user.personal_details.full_name = full_name
        user.personal_details.email = email

        user_id = await self._user_repo.create(user)
        logger.info("user_registered", user_id=user_id, email=email)
        return user_id

    async def login(self, *, email: str, password: str) -> dict[str, str]:
        """
        Authenticate a user and return a JWT token.

        Returns:
            Dict with access_token, token_type, user_id, email.

        Raises:
            AuthenticationError: If credentials are invalid.
        """
        user = await self._user_repo.find_by_email(email)

        if user is None:
            logger.warning("login_failed_user_not_found", email=email)
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, user.password):
            logger.warning("login_failed_bad_password", email=email)
            raise AuthenticationError("Invalid email or password")

        token = create_access_token({
            "user_id": user.id,
            "email": user.email,
            "role": user.role.value,
        })

        logger.info("user_logged_in", user_id=user.id, email=email)

        return {
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "email": user.email,
        }
