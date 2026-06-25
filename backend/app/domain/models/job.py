"""
Job Domain Model.

Rich entity representing a job listing with validation,
computed fingerprints, and business rules.
"""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, computed_field

from app.core.constants import JobSource, JobStatus, WorkType


class SalaryRange(BaseModel):
    """Structured salary information."""

    min_value: int | None = None
    max_value: int | None = None
    currency: str = "USD"

    @property
    def display(self) -> str:
        if self.min_value and self.max_value:
            return f"${self.min_value:,} - ${self.max_value:,} {self.currency}"
        if self.min_value:
            return f"${self.min_value:,}+ {self.currency}"
        if self.max_value:
            return f"Up to ${self.max_value:,} {self.currency}"
        return ""


class JobClassification(BaseModel):
    """AI-generated classification of a job listing."""

    is_relevant: bool = False
    category: str = ""
    subcategory: str = ""
    confidence: float = 0.0


class JDAnalysis(BaseModel):
    """Structured analysis of a job description."""

    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    experience_years: str = ""
    education: str = ""
    keywords: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    benefits: list[str] = Field(default_factory=list)
    work_type: str = ""


class JobModel(BaseModel):
    """
    Job domain entity — a normalized, deduplicated job listing.

    The fingerprint is computed from title + company to prevent duplicates.
    Status tracks progress through the career pipeline:
    new → classified → analyzed → matched → applied.
    """

    id: str = ""
    job_id: str = ""  # Source platform's ID

    title: str
    company: str
    location: str = ""
    description: str = ""

    skills: list[str] = Field(default_factory=list)
    salary: SalaryRange = Field(default_factory=SalaryRange)
    experience_required: str = ""
    work_type: WorkType = WorkType.UNKNOWN

    source: JobSource = JobSource.REMOTEOK
    url: str = ""
    posted_date: str = ""

    # Pipeline tracking
    status: JobStatus = JobStatus.NEW
    classification: JobClassification | None = None
    jd_analysis: JDAnalysis | None = None

    collected_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @computed_field  # type: ignore[prop-decorator]
    @property
    def fingerprint(self) -> str:
        """
        Deterministic dedup fingerprint.

        Combines normalized title + company into a SHA-256 hash.
        Two jobs from different sources with the same title and company
        will produce the same fingerprint.
        """
        raw = f"{self.title.lower().strip()}|{self.company.lower().strip()}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def is_valid_for_collection(self) -> bool:
        """Business rule: a job must meet minimum quality criteria."""
        if not self.title or not self.company:
            return False
        if len(self.description) < 100:
            return False
        return True

    def to_storage_dict(self) -> dict[str, Any]:
        """Serialize for database storage (includes computed fingerprint)."""
        data = self.model_dump()
        data["fingerprint"] = self.fingerprint
        return data
