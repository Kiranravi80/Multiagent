"""
V1 API Router Aggregator.

Combines all v1 routers under a single prefix.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.presentation.api.v1.agent_router import router as agent_router
from app.presentation.api.v1.auth_router import router as auth_router
from app.presentation.api.v1.job_router import router as job_router
from app.presentation.api.v1.profile_router import router as profile_router
from app.presentation.api.v1.resume_router import router as resume_router
from app.presentation.api.v1.system_router import router as system_router

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(profile_router)
v1_router.include_router(resume_router)
v1_router.include_router(job_router)
v1_router.include_router(agent_router)
v1_router.include_router(system_router)
