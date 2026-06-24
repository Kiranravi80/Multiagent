from fastapi import APIRouter, HTTPException
from app.schemas.user import UserCreate, UserUpdate
from app.services.user_service import (
    create_user,
    get_users,
    get_user,
    update_user,
    delete_user
)

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.post("/")
async def create_user_route(user: UserCreate):

    user_dict = user.model_dump()

    user_id = await create_user(user_dict)

    return {
        "message": "User created successfully",
        "id": user_id
    }


@router.get("/")
async def get_users_route():
    return await get_users()


@router.get("/{user_id}")
async def get_user_route(user_id: str):

    user = await get_user(user_id)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user


@router.put("/{user_id}")
async def update_user_route(
    user_id: str,
    user: UserUpdate
):

    updated_user = await update_user(
        user_id,
        user.model_dump(exclude_none=True)
    )

    return updated_user


@router.delete("/{user_id}")
async def delete_user_route(user_id: str):

    deleted = await delete_user(user_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "message": "User deleted successfully"
    }