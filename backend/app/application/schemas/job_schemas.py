"""Job Schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class JobResponse(BaseModel):
    id: str = ""
    title: str = ""
    company: str = ""
    location: str = ""
    description: str = ""
    skills: list[str] = Field(default_factory=list)
    salary: dict[str, Any] = Field(default_factory=dict)
    source: str = ""
    url: str = ""
    status: str = "new"
    work_type: str = "unknown"


class JobCollectionResponse(BaseModel):
    message: str = "Jobs collected"
    total_collected: int = 0
    new_jobs: int = 0
    duplicates_skipped: int = 0
