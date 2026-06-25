"""Learning Plan Domain Model.

Represents a structured roadmap created by PAIOS to guide the user in acquiring missing skills.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class LearningTask(BaseModel):
    """A specific study unit or assignment inside a learning plan."""

    topic: str
    description: str = ""
    estimated_hours: float = 1.0
    status: str = "pending"  # pending, in_progress, completed
    completed_at: datetime | None = None


class LearningPlanModel(BaseModel):
    """Roadmap mapping user skill gaps to actionable learning schedules."""

    id: str = ""
    user_id: str
    title: str
    target_skills: list[str] = Field(default_factory=list)
    tasks: list[LearningTask] = Field(default_factory=list)
    status: str = "not_started"  # not_started, in_progress, completed

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for storage."""
        data = self.model_dump(exclude={"id"})
        if self.id:
            data["_id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LearningPlanModel:
        """Create model from database dictionary."""
        doc = data.copy()
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)
