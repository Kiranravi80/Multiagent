"""Portfolio Domain Model.

Represents the user's portfolio layout configurations, biographical updates, and featured projects.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class PortfolioModel(BaseModel):
    """User portfolio configuration and layout metadata."""

    id: str = ""
    user_id: str
    bio: str = ""
    skills: list[str] = Field(default_factory=list)
    projects: list[dict[str, Any]] = Field(default_factory=list)
    socials: dict[str, str] = Field(default_factory=dict)
    layout: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for database storage."""
        data = self.model_dump(exclude={"id"})
        if self.id:
            data["_id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PortfolioModel:
        """Create model instance from database dictionary."""
        doc = data.copy()
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)
