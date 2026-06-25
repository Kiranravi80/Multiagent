"""Resume Schemas."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ResumeUploadResponse(BaseModel):
    message: str = "Resume uploaded successfully"
    linkedin: str = ""
    github: str = ""
    portfolio: str = ""


class ResumeParseResponse(BaseModel):
    message: str = "Resume parsed successfully"
    data: dict[str, Any] = Field(default_factory=dict)
