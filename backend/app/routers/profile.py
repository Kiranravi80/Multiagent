from fastapi import APIRouter
from fastapi import Depends
from app.database import db

from app.schemas.profile import UserProfileUpdate
from app.dependencies.auth import get_current_user

from app.services.profile_service import (
    get_profile,
    update_profile
)

router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)


@router.get("/me")
async def get_my_profile(
    current_user=Depends(get_current_user)
):

    return await get_profile(
        current_user["email"]
    )


@router.put("/me")
async def update_my_profile(
    profile: UserProfileUpdate,
    current_user=Depends(get_current_user)
):

    return await update_profile(
        current_user["email"],
        profile.model_dump(
            exclude_none=True
        )
    )


@router.get("/summary")
async def profile_summary(
    current_user=Depends(get_current_user)
):

    user = await db.users.find_one(
        {"email": current_user["email"]}
    )

    return {
        "name": user["personal_details"].get(
            "full_name"
        ),

        "skills_count": len(
            user.get("skills", [])
        ),

        "projects_count": len(
            user.get("projects", [])
        ),

        "experience_count": len(
            user.get("experience", [])
        ),

        "certifications_count": len(
            user.get("certifications", [])
        ),

        "achievements_count": len(
            user.get("achievements", [])
        ),

        "profile_completion": profile_completion(user)
    }

def profile_completion(user):

    score = 0

    if user.get("personal_details"):
        score += 15

    if user.get("education"):
        score += 15

    if user.get("skills"):
        score += 20

    if user.get("projects"):
        score += 15

    if user.get("experience"):
        score += 15

    if user.get("certifications"):
        score += 10

    if user.get("achievements"):
        score += 10

    
    return score
    