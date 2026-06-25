"""PAIOS Audit Service.

Subscribes to domain events and automatically writes them to the persistent audit trail.
"""

from __future__ import annotations

from typing import Any

from app.core.logging import get_logger
from app.domain.events.base import DomainEvent
from app.domain.models.audit_log import AuditLogModel
from app.domain.repositories.audit_repository import AuditRepository

logger = get_logger(__name__)


class AuditService:
    """Service to automatically process and persist audit trails from domain events."""

    def __init__(self, audit_repo: AuditRepository) -> None:
        self._audit_repo = audit_repo

    async def log_event(self, event: DomainEvent) -> None:
        """Callback handler to serialize a DomainEvent into an AuditLogModel.

        Args:
            event: The domain event published on the message bus.
        """
        try:
            # Map source and action name
            source = event.source_agent
            action = event.event_type.lower()
            
            # Map status
            status = "success"
            if "status" in event.payload:
                status = str(event.payload["status"])
            elif "error" in event.payload or "errors" in event.payload or "fail" in action:
                status = "failure"
                
            audit_entry = AuditLogModel(
                event_type=event.event_type,
                source=source,
                action=action,
                status=status,
                payload=event.payload,
                correlation_id=event.correlation_id,
                timestamp=event.timestamp,
            )
            
            await self._audit_repo.create(audit_entry)
            logger.debug("audit_log_created", event_type=event.event_type, action=action)
        except Exception as exc:
            logger.error("audit_logging_failed", event_id=event.event_id, error=str(exc))
