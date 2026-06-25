"""Digest Domain Model.

Repines AI-generated digests and reports summarizing career, tech trends, and research.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class DigestModel(BaseModel):
    """Normalized digest entry containing summarized updates."""

    id: str = ""
    title: str
    type: str = "daily"  # daily, weekly, monthly, opportunity
    summary: str = ""

    news_highlights: list[dict[str, Any]] = Field(default_factory=list)
    startup_discoveries: list[dict[str, Any]] = Field(default_factory=list)
    github_trends: list[dict[str, Any]] = Field(default_factory=list)
    research_papers: list[dict[str, Any]] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for storage."""
        data = self.model_dump(exclude={"id"})
        if self.id:
            data["_id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DigestModel:
        """Create model from database dictionary."""
        doc = data.copy()
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)
