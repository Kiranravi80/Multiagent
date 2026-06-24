from fastapi import APIRouter, HTTPException
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest
)

from app.services.auth_service import (
    register_user,
    login_user
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/register")
async def register(
    user: RegisterRequest
):

    user_id = await register_user(
        user.model_dump()
    )

    if not user_id:
        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    return {
        "message": "User registered",
        "user_id": user_id
    }


@router.post("/login")
async def login(
    credentials: LoginRequest
):

    token = await login_user(
        credentials.email,
        credentials.password
    )

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    return {
        "access_token": token,
        "token_type": "bearer"
    }