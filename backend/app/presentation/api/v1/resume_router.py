"""Resume Router — /api/v1/resume endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, File, UploadFile

from app.application.dependencies.auth import get_current_user
from app.application.dependencies.container import get_container

router = APIRouter(prefix="/resume", tags=["Resume"])


@router.post("/upload")
async def upload_resume(
    file: UploadFile = File(...),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    container = get_container()
    content = await file.read()

    return await container.resume_service.upload_resume(
        user_id=current_user["user_id"],
        email=current_user["email"],
        filename=file.filename or "resume.pdf",
        content=content,
    )


@router.post("/parse")
async def parse_resume(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    container = get_container()
    return await container.resume_service.parse_resume(email=current_user["email"])
