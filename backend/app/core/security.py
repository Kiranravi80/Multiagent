"""
PAIOS Security Utilities.

Provides:
- Password hashing (bcrypt via passlib)
- JWT token creation and verification
- Fernet symmetric encryption for PII/credentials

All configuration comes from centralized Settings — no os.getenv().
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from cryptography.fernet import Fernet, InvalidToken
from passlib.context import CryptContext

from app.core.config import get_settings
from app.core.exceptions import AuthenticationError
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Password Hashing ──────────────────────────────────────────────────────

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return _pwd_context.verify(plain_password, hashed_password)


# ── JWT Tokens ─────────────────────────────────────────────────────────────


def create_access_token(data: dict[str, Any], *, expires_delta: timedelta | None = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        data: Claims to encode (must include 'user_id' and 'email').
        expires_delta: Custom expiry. Defaults to Settings.access_token_expire_minutes.

    Returns:
        Encoded JWT string.
    """
    settings = get_settings()
    payload = data.copy()

    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_expire_minutes)

    payload["exp"] = datetime.now(UTC) + expires_delta
    payload["iat"] = datetime.now(UTC)

    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Args:
        token: The raw JWT string.

    Returns:
        Decoded payload dict.

    Raises:
        AuthenticationError: If the token is invalid or expired.
    """
    settings = get_settings()

    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("token_expired")
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as exc:
        logger.warning("token_invalid", error=str(exc))
        raise AuthenticationError("Invalid token")


# ── Fernet Encryption ─────────────────────────────────────────────────────


def _get_fernet() -> Fernet | None:
    """Return a Fernet instance if encryption key is configured."""
    settings = get_settings()
    if not settings.encryption_key:
        return None
    return Fernet(settings.encryption_key.encode())


def encrypt_value(plaintext: str) -> str:
    """
    Encrypt a string using Fernet symmetric encryption.

    Returns the plaintext unchanged if no encryption key is configured.
    """
    fernet = _get_fernet()
    if fernet is None:
        logger.debug("encryption_skipped", reason="no encryption key configured")
        return plaintext
    return fernet.encrypt(plaintext.encode()).decode()


def decrypt_value(ciphertext: str) -> str:
    """
    Decrypt a Fernet-encrypted string.

    Returns the ciphertext unchanged if no encryption key is configured.

    Raises:
        PAIOSException: If decryption fails (wrong key or corrupted data).
    """
    fernet = _get_fernet()
    if fernet is None:
        return ciphertext
    try:
        return fernet.decrypt(ciphertext.encode()).decode()
    except InvalidToken:
        logger.error("decryption_failed", reason="invalid token or wrong key")
        raise AuthenticationError("Failed to decrypt value — check encryption key")
