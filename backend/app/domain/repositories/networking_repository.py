"""Networking Repository Interface.

Defines the contract for professional connections and outreach logs.
"""

from __future__ import annotations

from abc import ABC
from app.domain.models.networking import NetworkingModel
from app.domain.repositories.base import BaseRepository


class NetworkingRepository(BaseRepository[NetworkingModel], ABC):
    """Repository interface for professional relationship tracking."""
    ...
