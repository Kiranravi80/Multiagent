"""Calendar Event Domain Model.

Represents scheduled meetings, interviews, mock sessions, and recruiter hold slots.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class CalendarEventModel(BaseModel):
    """Calendar event containing schedules and participants."""

    id: str = ""
    title: str
    description: str | None = None
    start_time: datetime
    end_time: datetime
    attendees: list[str] = Field(default_factory=list)
    meeting_link: str | None = None
    status: str = "scheduled"  # scheduled, cancelled, completed
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for database storage."""
        data = self.model_dump(exclude={"id"})
        if self.id:
            data["_id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CalendarEventModel:
        """Create model instance from database dictionary."""
        doc = data.copy()
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)
