"""Audit Log Domain Model.

Represents an entry in the system audit trail.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class AuditLogModel(BaseModel):
    """
    Standard audit log entry.
    
    Tracks system events, user actions, and agent executions for compliance and monitoring.
    """

    id: str = ""
    event_type: str
    source: str  # e.g., "user_id", "agent_name", "system"
    action: str  # e.g., "login", "create_job", "tailor_resume"
    status: str  # e.g., "success", "failure", "pending"
    payload: dict[str, Any] = Field(default_factory=dict)
    correlation_id: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ip_address: str | None = None
    user_agent: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary for storage."""
        data = self.model_dump(exclude={"id"})
        if self.id:
            data["_id"] = self.id
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AuditLogModel:
        """Create model from database dictionary."""
        doc = data.copy()
        if "_id" in doc:
            doc["id"] = str(doc.pop("_id"))
        return cls(**doc)
