"""Knowledge Domain Model.

Represents a single knowledge element (arXiv paper, GitHub repo, Tech news) gathered by agents.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class KnowledgeModel(BaseModel):
    """General knowledge item representing external insights."""

    id: str = ""
    title: str
    type: str  # paper, repository, startup, news
    summary: str = ""
    url: str = ""
    
    metadata_fields: dict[str, Any] = Field(default_factory=dict, alias="metadata")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for storage."""
        data = self.model_dump(exclude={"id"})
        if self.id:
            data["_id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> KnowledgeModel:
        """Create model from database dictionary."""
        doc = data.copy()
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)
