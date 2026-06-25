"""
User Domain Model.

Rich entity with validation rules and computed properties.
This is the canonical representation of a user — all layers map to/from this.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from app.core.constants import UserRole


class PersonalDetails(BaseModel):
    """User personal information."""

    full_name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""


class SocialProfiles(BaseModel):
    """User social/professional links."""

    linkedin: str = ""
    github: str = ""
    portfolio: str = ""


class Education(BaseModel):
    """A single education entry."""

    institution: str = ""
    degree: str = ""
    field_of_study: str = ""
    start_date: str = ""
    end_date: str = ""
    grade: str = ""
    description: str = ""


class Experience(BaseModel):
    """A single work experience entry."""

    company: str = ""
    title: str = ""
    location: str = ""
    start_date: str = ""
    end_date: str = ""
    is_current: bool = False
    description: str = ""
    technologies: list[str] = Field(default_factory=list)


class Project(BaseModel):
    """A single project entry."""

    name: str = ""
    description: str = ""
    technologies: list[str] = Field(default_factory=list)
    url: str = ""
    github_url: str = ""
    start_date: str = ""
    end_date: str = ""


class Certification(BaseModel):
    """A single certification entry."""

    name: str = ""
    issuer: str = ""
    date: str = ""
    url: str = ""
    credential_id: str = ""


class UserPreferences(BaseModel):
    """User job search preferences."""

    job_types: list[str] = Field(default_factory=list)
    preferred_locations: list[str] = Field(default_factory=list)
    salary_range_min: int | None = None
    salary_range_max: int | None = None
    salary_currency: str = "USD"
    preferred_industries: list[str] = Field(default_factory=list)
    open_to_remote: bool = True
    open_to_relocation: bool = False


class CareerAnalysis(BaseModel):
    """AI-generated career analysis of the user profile."""

    experience_level: str = ""
    total_experience_years: float = 0.0
    primary_domain: str = ""
    secondary_domains: list[str] = Field(default_factory=list)
    recommended_roles: list[str] = Field(default_factory=list)
    core_skills: list[str] = Field(default_factory=list)
    missing_skills: list[str] = Field(default_factory=list)
    career_stage: str = ""
    analyzed_at: datetime | None = None


class UserModel(BaseModel):
    """
    User domain entity — the canonical representation of a PAIOS user.

    This model contains all user data: profile, skills, experience,
    career analysis, and preferences. It is never directly exposed
    to the API — schemas map to/from this.
    """

    id: str = ""
    email: str = ""
    password: str = ""  # bcrypt hash, never exposed
    full_name: str = ""
    role: UserRole = UserRole.USER

    personal_details: PersonalDetails = Field(default_factory=PersonalDetails)
    social_profiles: SocialProfiles = Field(default_factory=SocialProfiles)

    education: list[Education] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)

    career_analysis: CareerAnalysis | None = None
    preferences: UserPreferences = Field(default_factory=UserPreferences)

    # Resume metadata (separate resume collection stores full data)
    resume_text: str = ""
    resume_file_path: str = ""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_safe_dict(self) -> dict[str, Any]:
        """Return a dict with sensitive fields removed (password, resume_text)."""
        data = self.model_dump()
        data.pop("password", None)
        data.pop("resume_text", None)
        return data
