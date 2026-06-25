"""Auth Router — /api/v1/auth endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.application.dependencies.container import get_container
from app.application.schemas.auth_schemas import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=RegisterResponse)
async def register(body: RegisterRequest) -> RegisterResponse:
    container = get_container()
    user_id = await container.auth_service.register(
        full_name=body.full_name,
        email=body.email,
        password=body.password,
    )
    return RegisterResponse(user_id=user_id)


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    container = get_container()
    result = await container.auth_service.login(
        email=body.email,
        password=body.password,
    )
    return TokenResponse(**result)
