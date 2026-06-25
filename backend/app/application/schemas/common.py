"""
Common Response Schemas.

Standard response wrappers used across all API endpoints.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool = True
    message: str = ""
    data: T | None = None


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    error: str
    code: str = "ERROR"
    details: dict[str, Any] = Field(default_factory=dict)


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list response."""

    success: bool = True
    data: list[T] = Field(default_factory=list)
    total: int = 0
    skip: int = 0
    limit: int = 100
    has_more: bool = False
