"""
Match Scoring Service.

Pure domain logic for scoring how well a user profile matches a job.
No AI calls — this is deterministic scoring based on overlapping data.
"""

from __future__ import annotations

from typing import Any


def calculate_skill_match(user_skills: list[str], job_skills: list[str]) -> float:
    """
    Calculate skill overlap score (0.0 to 1.0).

    Uses normalized, case-insensitive comparison.
    """
    if not job_skills:
        return 1.0  # No requirements = automatic match

    user_set = {s.lower().strip() for s in user_skills}
    job_set = {s.lower().strip() for s in job_skills}

    if not job_set:
        return 1.0

    intersection = user_set & job_set
    return len(intersection) / len(job_set)


def calculate_experience_match(
    user_years: float,
    required_years: float,
) -> float:
    """
    Calculate experience match score (0.0 to 1.0).

    Overqualified (1+ extra years) still returns 1.0.
    Under-qualified scales linearly.
    """
    if required_years <= 0:
        return 1.0

    if user_years >= required_years:
        return 1.0

    return max(0.0, user_years / required_years)


def calculate_overall_match(
    *,
    skill_score: float,
    experience_score: float,
    education_score: float = 1.0,
    location_score: float = 1.0,
    salary_score: float = 1.0,
    culture_score: float = 1.0,
) -> float:
    """
    Calculate weighted overall match score (0.0 to 1.0).

    Weights:
        Skills: 35%
        Experience: 25%
        Education: 10%
        Location: 10%
        Salary: 10%
        Culture: 10%
    """
    return (
        skill_score * 0.35
        + experience_score * 0.25
        + education_score * 0.10
        + location_score * 0.10
        + salary_score * 0.10
        + culture_score * 0.10
    )


def match_to_dict(
    *,
    skill_score: float,
    experience_score: float,
    education_score: float = 1.0,
    location_score: float = 1.0,
    salary_score: float = 1.0,
    culture_score: float = 1.0,
) -> dict[str, float]:
    """Return all match scores as a dict, including the overall score."""
    overall = calculate_overall_match(
        skill_score=skill_score,
        experience_score=experience_score,
        education_score=education_score,
        location_score=location_score,
        salary_score=salary_score,
        culture_score=culture_score,
    )
    return {
        "overall": round(overall, 4),
        "skill": round(skill_score, 4),
        "experience": round(experience_score, 4),
        "education": round(education_score, 4),
        "location": round(location_score, 4),
        "salary": round(salary_score, 4),
        "culture": round(culture_score, 4),
    }
