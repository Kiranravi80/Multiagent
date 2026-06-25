"""
Profile Domain Model.

Lightweight aggregate used for profile operations
(separate from the full UserModel for Separation of Concerns).
"""

from __future__ import annotations

from app.domain.models.user import (
    CareerAnalysis,
    Certification,
    Education,
    Experience,
    PersonalDetails,
    Project,
    SocialProfiles,
    UserPreferences,
)


# Profile is a read-model / view built from User.
# Re-export the component models for convenience.
__all__ = [
    "PersonalDetails",
    "SocialProfiles",
    "Education",
    "Experience",
    "Project",
    "Certification",
    "CareerAnalysis",
    "UserPreferences",
]
