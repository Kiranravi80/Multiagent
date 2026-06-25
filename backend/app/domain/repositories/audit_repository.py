"""Audit Repository Interface.

Defines the contract for persisting and querying system audit logs.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.domain.models.audit_log import AuditLogModel
from app.domain.repositories.base import BaseRepository


class AuditRepository(BaseRepository[AuditLogModel], ABC):
    """Repository interface for Audit Logs."""

    @abstractmethod
    async def get_by_source(
        self,
        source: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLogModel]:
        """Retrieve audit logs produced by a specific source."""
        ...

    @abstractmethod
    async def get_by_action(
        self,
        action: str,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> list[AuditLogModel]:
        """Retrieve audit logs of a specific action type."""
        ...
