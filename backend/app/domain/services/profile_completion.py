"""
Profile Completion Scoring.

Pure domain logic — no database, no AI, no infrastructure dependencies.
Migrated from the router file where it was incorrectly placed.
"""

from __future__ import annotations

from typing import Any

# Weight configuration for profile sections
_SECTION_WEIGHTS: dict[str, int] = {
    "personal_details": 15,
    "education": 15,
    "skills": 20,
    "projects": 15,
    "experience": 15,
    "certifications": 10,
    "achievements": 10,
}


def calculate_profile_completion(user_data: dict[str, Any]) -> int:
    """
    Calculate a 0-100 profile completion score based on filled sections.

    This is a simple presence check — it does not evaluate quality.
    Future versions will add quality scoring (e.g., description length,
    number of skills, years of experience).

    Args:
        user_data: User document dict (from DB or domain model).

    Returns:
        Integer score between 0 and 100.
    """
    score = 0

    for section, weight in _SECTION_WEIGHTS.items():
        value = user_data.get(section)

        if value is None:
            continue

        # Dicts: check if any field has a value
        if isinstance(value, dict):
            if any(v for v in value.values()):
                score += weight

        # Lists: check if non-empty
        elif isinstance(value, list):
            if len(value) > 0:
                score += weight

        # Strings: check if non-empty
        elif isinstance(value, str):
            if value.strip():
                score += weight

        # Anything truthy
        elif value:
            score += weight

    return min(score, 100)


def get_missing_sections(user_data: dict[str, Any]) -> list[str]:
    """
    Return a list of profile sections that are empty or missing.

    Useful for prompting the user to complete their profile.
    """
    missing: list[str] = []

    for section in _SECTION_WEIGHTS:
        value = user_data.get(section)
        if value is None:
            missing.append(section)
        elif isinstance(value, (list, dict)) and not value:
            missing.append(section)
        elif isinstance(value, str) and not value.strip():
            missing.append(section)

    return missing
