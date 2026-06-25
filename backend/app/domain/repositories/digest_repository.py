"""Digest Repository Interface.

Defines the contract for generated digests and reports.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from app.domain.models.digest import DigestModel
from app.domain.repositories.base import BaseRepository


class DigestRepository(BaseRepository[DigestModel], ABC):
    """Repository interface for system digests."""

    @abstractmethod
    async def get_latest_by_type(self, digest_type: str) -> DigestModel | None:
        """Fetch the latest digest of a specific type (daily, weekly, monthly)."""
        ...
