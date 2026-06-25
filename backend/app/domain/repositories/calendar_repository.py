"""Calendar Repository Interface.

Defines the contract for scheduled meetings and interview hold operations.
"""

from __future__ import annotations

from abc import ABC
from app.domain.models.calendar import CalendarEventModel
from app.domain.repositories.base import BaseRepository


class CalendarRepository(BaseRepository[CalendarEventModel], ABC):
    """Repository interface for calendar schedules."""
    ...
