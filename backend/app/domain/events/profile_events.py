"""
Profile Domain Events.
"""

from __future__ import annotations

from typing import Any

from app.core.constants import EventType
from app.domain.events.base import DomainEvent


def profile_updated_event(*, source: str, user_id: str, fields: list[str]) -> DomainEvent:
    """Published when a user profile is updated."""
    return DomainEvent(
        event_type=EventType.PROFILE_UPDATED,
        source_agent=source,
        payload={"user_id": user_id, "updated_fields": fields},
    )


def profile_analyzed_event(
    *, source: str, user_id: str, analysis: dict[str, Any]
) -> DomainEvent:
    """Published when AI analysis of a user profile is completed."""
    return DomainEvent(
        event_type=EventType.PROFILE_ANALYZED,
        source_agent=source,
        payload={"user_id": user_id, "analysis": analysis},
    )


def resume_uploaded_event(*, source: str, user_id: str, filename: str) -> DomainEvent:
    """Published when a user uploads a resume file."""
    return DomainEvent(
        event_type=EventType.RESUME_UPLOADED,
        source_agent=source,
        payload={"user_id": user_id, "filename": filename},
    )


def resume_parsed_event(
    *, source: str, user_id: str, sections_found: list[str]
) -> DomainEvent:
    """Published when a resume is parsed into structured data."""
    return DomainEvent(
        event_type=EventType.RESUME_PARSED,
        source_agent=source,
        payload={"user_id": user_id, "sections_found": sections_found},
    )
