from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File
from fastapi import Depends
from datetime import datetime
import os
import aiofiles

from app.database import db
from app.dependencies.auth import get_current_user

from app.services.resume_service import (
    extract_text_from_pdf,
    extract_links
)
from app.services.resume_parser_service import (
    parse_resume_with_ai
)

router = APIRouter(
    prefix="/resume",
    tags=["Resume"]
)


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user)
):

    os.makedirs(
        "uploads/resumes",
        exist_ok=True
    )

    filename = (
        f"{current_user['user_id']}_"
        f"{file.filename}"
    )

    file_path = (
        f"uploads/resumes/{filename}"
    )

    async with aiofiles.open(
        file_path,
        "wb"
    ) as out_file:

        content = await file.read()

        await out_file.write(content)

    resume_text = extract_text_from_pdf(
        file_path
    )
    print(resume_text[:3000])

    links = extract_links(
        resume_text
    )

    await db.users.update_one(
        {
            "email": current_user["email"]
        },
        {
            "$set": {
                "resume.file_name": file.filename,
                "resume.file_path": file_path,
                "resume.uploaded_at": datetime.utcnow(),

                "social_profiles.linkedin":
                    links["linkedin"],

                "social_profiles.github":
                    links["github"],

                "social_profiles.portfolio":
                    links["portfolio"],

                "resume_text": resume_text
            }
        }
    )

    return {
        "message":
            "Resume uploaded successfully",

        "linkedin":
            links["linkedin"],

        "github":
            links["github"],

        "portfolio":
            links["portfolio"]
    }

    
@router.post("/parse")
async def parse_resume(
    current_user=Depends(get_current_user)
):

    user = await db.users.find_one(
        {
            "email": current_user["email"]
        }
    )

    if not user:
        return {
            "error": "User not found"
        }

    resume_text = user.get(
        "resume_text",
        ""
    )

    if not resume_text:
        return {
            "error": "Resume not uploaded"
        }

    parsed_data = await parse_resume_with_ai(
        resume_text
    )

    await db.users.update_one(
        {
            "_id": user["_id"]
        },
        {
            "$set": {
                "personal_details": parsed_data.get(
                    "personal_details", {}
                ),

                "social_profiles": parsed_data.get(
                    "social_profiles", {}
                ),

                "education": parsed_data.get(
                    "education", []
                ),

                "skills": parsed_data.get(
                    "skills", []
                ),

                "projects": parsed_data.get(
                    "projects", []
                ),

                "experience": parsed_data.get(
                    "experience", []
                ),

                "certifications": parsed_data.get(
                    "certifications", []
                ),

                "achievements": parsed_data.get(
                    "achievements", []
                )
            }
        }
    )

    return {
    "message": "Profile parsed successfully",
    "data": parsed_data
}