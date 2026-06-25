"""
Auth Dependency — FastAPI dependency for JWT authentication.

Replaces app/dependencies/auth.py.
Uses centralized security module instead of raw os.getenv().
"""

from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import AuthenticationError
from app.core.security import decode_access_token

_security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_security),
) -> dict[str, Any]:
    """
    FastAPI dependency: extract and validate the JWT bearer token.

    Returns:
        Decoded token payload with user_id, email, role.

    Raises:
        HTTPException 401: If token is missing, invalid, or expired.
    """
    try:
        payload = decode_access_token(credentials.credentials)
        return payload
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
