"""User Schemas — request/response DTOs for user endpoints."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr
from typing import Optional


class UserCreateRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str = ""


class UserUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    full_name: str = ""
    email: str
    phone: str = ""
    role: str = "user"
