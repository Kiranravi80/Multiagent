"""
Career Domain Events.

Typed event factories for the career processing pipeline:
Job Collection → Classification → JD Analysis → Matching → ATS → Application.
"""

from __future__ import annotations

from typing import Any

from app.core.constants import EventType
from app.domain.events.base import DomainEvent


def job_collected_event(
    *,
    source: str,
    job_count: int,
    source_platform: str,
    correlation_id: str = "",
) -> DomainEvent:
    """Published when jobs are collected from a source."""
    return DomainEvent(
        event_type=EventType.JOB_COLLECTED,
        source_agent=source,
        payload={
            "job_count": job_count,
            "source_platform": source_platform,
        },
        **({"correlation_id": correlation_id} if correlation_id else {}),
    )


def job_classified_event(
    *,
    source: str,
    job_id: str,
    is_relevant: bool,
    category: str,
    confidence: float,
    correlation_id: str = "",
) -> DomainEvent:
    """Published when a job is classified as relevant/irrelevant."""
    return DomainEvent(
        event_type=EventType.JOB_CLASSIFIED,
        source_agent=source,
        payload={
            "job_id": job_id,
            "is_relevant": is_relevant,
            "category": category,
            "confidence": confidence,
        },
        **({"correlation_id": correlation_id} if correlation_id else {}),
    )


def jd_analyzed_event(
    *,
    source: str,
    job_id: str,
    analysis: dict[str, Any],
    correlation_id: str = "",
) -> DomainEvent:
    """Published when a job description is analyzed into structured data."""
    return DomainEvent(
        event_type=EventType.JD_ANALYZED,
        source_agent=source,
        payload={"job_id": job_id, "analysis": analysis},
        **({"correlation_id": correlation_id} if correlation_id else {}),
    )


def job_matched_event(
    *,
    source: str,
    job_id: str,
    user_id: str,
    match_score: dict[str, float],
    correlation_id: str = "",
) -> DomainEvent:
    """Published when a job is scored against a user profile."""
    return DomainEvent(
        event_type=EventType.JOB_MATCHED,
        source_agent=source,
        payload={
            "job_id": job_id,
            "user_id": user_id,
            "match_score": match_score,
        },
        **({"correlation_id": correlation_id} if correlation_id else {}),
    )


def ats_completed_event(
    *,
    source: str,
    resume_id: str,
    job_id: str,
    ats_score: float,
    improvements: list[str],
    correlation_id: str = "",
) -> DomainEvent:
    """Published when an ATS evaluation is completed."""
    return DomainEvent(
        event_type=EventType.ATS_COMPLETED,
        source_agent=source,
        payload={
            "resume_id": resume_id,
            "job_id": job_id,
            "ats_score": ats_score,
            "improvements": improvements,
        },
        **({"correlation_id": correlation_id} if correlation_id else {}),
    )


def resume_generated_event(
    *,
    source: str,
    resume_id: str,
    resume_type: str,
    user_id: str,
    correlation_id: str = "",
) -> DomainEvent:
    """Published when a tailored resume is generated."""
    return DomainEvent(
        event_type=EventType.RESUME_GENERATED,
        source_agent=source,
        payload={
            "resume_id": resume_id,
            "resume_type": resume_type,
            "user_id": user_id,
        },
        **({"correlation_id": correlation_id} if correlation_id else {}),
    )


def application_ready_event(
    *,
    source: str,
    job_id: str,
    user_id: str,
    resume_id: str,
    match_score: float,
    correlation_id: str = "",
) -> DomainEvent:
    """Published when an application is ready for user approval."""
    return DomainEvent(
        event_type=EventType.APPLICATION_READY,
        source_agent=source,
        payload={
            "job_id": job_id,
            "user_id": user_id,
            "resume_id": resume_id,
            "match_score": match_score,
        },
        **({"correlation_id": correlation_id} if correlation_id else {}),
    )
