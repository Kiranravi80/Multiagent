"""
Resume Domain Model.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field

from app.core.constants import ResumeType


class ResumeModel(BaseModel):
    """A resume variant (original or tailored)."""

    id: str = ""
    user_id: str = ""
    type: ResumeType = ResumeType.ORIGINAL

    file_name: str = ""
    file_path: str = ""
    raw_text: str = ""
    parsed_data: dict[str, Any] = Field(default_factory=dict)

    tailored_for_job_id: str | None = None
    ats_score: float | None = None

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
