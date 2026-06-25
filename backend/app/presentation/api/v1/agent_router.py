"""Agent Router — /api/v1/agents endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.application.dependencies.auth import get_current_user
from app.application.dependencies.container import get_container
from app.application.schemas.agent_schemas import AgentExecuteRequest

router = APIRouter(prefix="/agents", tags=["AI Agents"])


@router.get("/status")
async def get_all_agent_status(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Get health status of all registered agents."""
    container = get_container()
    return await container.agent_orchestration_service.get_system_status()


@router.post("/execute")
async def execute_agent(
    body: AgentExecuteRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Trigger execution of a specific agent."""
    container = get_container()
    result = await container.agent_orchestration_service.execute_agent(
        body.agent_name, context=body.context
    )
    return {
        "success": result.success,
        "agent_name": body.agent_name,
        "message": result.message,
        "data": result.data,
    }


@router.post("/analyze-profile")
async def analyze_profile(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Run AI profile analysis for the current user."""
    container = get_container()
    user = await container.user_repo.find_by_email(current_user["email"])

    if user is None:
        from app.core.exceptions import EntityNotFoundError
        raise EntityNotFoundError("User", current_user["email"])

    profile_data = {
        "education": [e.model_dump() for e in user.education],
        "skills": user.skills,
        "projects": [p.model_dump() for p in user.projects],
        "experience": [e.model_dump() for e in user.experience],
        "certifications": [c.model_dump() for c in user.certifications],
        "achievements": user.achievements,
    }

    analysis = await container.llm_service.analyze_profile(profile_data)
    await container.user_repo.update_career_analysis(user.id, analysis)

    return analysis


@router.get("/summary")
async def daily_summary(
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict:
    """Get daily execution summary."""
    container = get_container()
    return await container.agent_orchestration_service.get_daily_summary()
