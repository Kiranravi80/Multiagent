"""Agent Schemas — request/response DTOs for agent endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgentStatusResponse(BaseModel):
    agent_name: str
    status: str
    healthy: bool = True
    last_execution: str | None = None
    error_count: int = 0
    metrics: dict[str, Any] = Field(default_factory=dict)


class AgentExecuteRequest(BaseModel):
    agent_name: str
    context: dict[str, Any] = Field(default_factory=dict)


class AgentExecuteResponse(BaseModel):
    success: bool
    agent_name: str
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)


class SystemStatusResponse(BaseModel):
    status: str = "healthy"
    agents_total: int = 0
    agents_healthy: int = 0
    agents_unhealthy: int = 0
    agents: dict[str, Any] = Field(default_factory=dict)
    started_at: str | None = None
