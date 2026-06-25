"""Networking Domain Model.

Represents target connections, recruiters, connection notes, and outreach histories.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class NetworkingModel(BaseModel):
    """Professional relationship and outreach tracker."""

    id: str = ""
    name: str
    role: str = ""
    company: str = ""
    linkedin_url: str | None = None
    email: str | None = None
    status: str = "identified"  # identified, outreach_drafted, outreach_sent, replied, connected, archived
    interaction_history: list[dict[str, Any]] = Field(default_factory=list)
    next_followup: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for database storage."""
        data = self.model_dump(exclude={"id"})
        if self.id:
            data["_id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NetworkingModel:
        """Create model instance from database dictionary."""
        doc = data.copy()
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)
