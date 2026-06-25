"""Interview Domain Model.

Represents an interactive mock interview prep session containing questions, user answers, and AI evaluations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class InterviewModel(BaseModel):
    """Interview preparation and evaluation record."""

    id: str = ""
    job_id: str | None = None
    role: str
    company: str
    questions: list[dict[str, Any]] = Field(default_factory=list)
    overall_feedback: str | None = None
    score: float | None = None
    status: str = "created"  # created, in_progress, completed
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for database storage."""
        data = self.model_dump(exclude={"id"})
        if self.id:
            data["_id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InterviewModel:
        """Create model instance from database dictionary."""
        doc = data.copy()
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)
