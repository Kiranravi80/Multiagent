"""Job Router — /api/v1/jobs endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from app.application.dependencies.auth import get_current_user
from app.application.dependencies.container import get_container

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/")
async def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: str | None = None,
    source: str | None = None,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    container = get_container()
    return await container.job_service.get_jobs(
        skip=skip, limit=limit, status=status, source=source
    )


@router.get("/stats")
async def job_stats(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    container = get_container()
    return await container.job_service.get_stats()


@router.get("/{job_id}")
async def get_job(
    job_id: str,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    container = get_container()
    job = await container.job_service.get_job(job_id)
    if job is None:
        from app.core.exceptions import EntityNotFoundError
        raise EntityNotFoundError("Job", job_id)
    return job
