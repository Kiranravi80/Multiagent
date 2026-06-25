"""Email Domain Model.

Represents email communication history, including inbound/outbound items, threads, and sending statuses.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class EmailModel(BaseModel):
    """Email correspondence log and draft queue entry."""

    id: str = ""
    thread_id: str | None = None
    to_email: str
    from_email: str
    subject: str
    body: str
    status: str = "draft"  # draft, pending_approval, queued, sent, received
    type: str = "outbound"  # outbound, inbound
    sent_at: datetime | None = None
    received_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for database storage."""
        data = self.model_dump(exclude={"id"})
        if self.id:
            data["_id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> EmailModel:
        """Create model instance from database dictionary."""
        doc = data.copy()
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)
