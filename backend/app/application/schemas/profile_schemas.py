"""Profile Schemas — request/response DTOs for profile endpoints."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None


class ProfileSummaryResponse(BaseModel):
    name: str = ""
    skills_count: int = 0
    projects_count: int = 0
    experience_count: int = 0
    certifications_count: int = 0
    achievements_count: int = 0
    profile_completion: int = 0
    missing_sections: list[str] = Field(default_factory=list)


class ProfileResponse(BaseModel):
    """Full profile data (excludes password and resume_text)."""

    id: str = ""
    email: str = ""
    full_name: str = ""
    personal_details: dict[str, Any] = Field(default_factory=dict)
    social_profiles: dict[str, Any] = Field(default_factory=dict)
    education: list[dict[str, Any]] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    experience: list[dict[str, Any]] = Field(default_factory=list)
    certifications: list[dict[str, Any]] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)
    career_analysis: dict[str, Any] | None = None
    preferences: dict[str, Any] = Field(default_factory=dict)
