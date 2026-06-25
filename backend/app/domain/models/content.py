"""Content Domain Model.

Represents technical articles, professional posts, and social updates drafted or published by PAIOS.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class ContentModel(BaseModel):
    """Professional content draft or publication entry."""

    id: str = ""
    platform: str  # linkedin, github, devto, medium, portfolio
    title: str
    body: str
    status: str = "draft"  # draft, pending_approval, approved, published
    approved_at: datetime | None = None
    published_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for database storage."""
        data = self.model_dump(exclude={"id"})
        if self.id:
            data["_id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContentModel:
        """Create model instance from database dictionary."""
        doc = data.copy()
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)
