from fastapi import APIRouter
from fastapi import Depends

from app.database import db

from app.dependencies.auth import (
    get_current_user
)

from app.services.profile_analyzer import (
    analyze_profile
)

router = APIRouter(
    prefix="/agent",
    tags=["AI Agents"]
)

@router.post("/analyze-profile")
async def analyze_user_profile(
    current_user=Depends(
        get_current_user
    )
):

    user = await db.users.find_one(
        {
            "email":
            current_user["email"]
        }
    )

    if not user:
        return {
            "error":
            "User not found"
        }

    profile_data = {
        "education":
        user.get(
            "education",
            []
        ),

        "skills":
        user.get(
            "skills",
            []
        ),

        "projects":
        user.get(
            "projects",
            []
        ),

        "experience":
        user.get(
            "experience",
            []
        ),

        "certifications":
        user.get(
            "certifications",
            []
        ),

        "achievements":
        user.get(
            "achievements",
            []
        )
    }

    analysis = await analyze_profile(
        profile_data
    )

    await db.users.update_one(
        {
            "_id":
            user["_id"]
        },
        {
            "$set": {
                "career_analysis":
                analysis
            }
        }
    )

    return analysis