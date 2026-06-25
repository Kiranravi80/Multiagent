"""
Application Domain Model.

Represents a job application with full lifecycle tracking.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from app.core.constants import ApplicationStatus


class MatchScore(BaseModel):
    """Detailed match scores between a user profile and a job."""

    overall: float = 0.0
    skill: float = 0.0
    experience: float = 0.0
    education: float = 0.0
    location: float = 0.0
    salary: float = 0.0
    culture: float = 0.0


class TimelineEntry(BaseModel):
    """A single status change in the application history."""

    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    notes: str = ""


class ApplicationModel(BaseModel):
    """
    Application domain entity — tracks a job application from match to outcome.

    Every status change is recorded in the timeline for audit purposes.
    """

    id: str = ""
    user_id: str = ""
    job_id: str = ""

    match_score: MatchScore = Field(default_factory=MatchScore)
    resume_version_id: str = ""
    ats_score: float | None = None

    status: ApplicationStatus = ApplicationStatus.PENDING_APPROVAL
    applied_at: datetime | None = None

    timeline: list[TimelineEntry] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def transition_status(self, new_status: ApplicationStatus, *, notes: str = "") -> None:
        """Record a status transition in the timeline."""
        self.status = new_status
        self.updated_at = datetime.now(UTC)
        self.timeline.append(
            TimelineEntry(status=new_status.value, notes=notes)
        )
