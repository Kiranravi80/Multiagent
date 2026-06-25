import pytest
from unittest.mock import AsyncMock

from app.application.services.audit_service import AuditService
from app.domain.events.base import DomainEvent


@pytest.mark.asyncio
async def test_audit_service_log_event() -> None:
    mock_repo = AsyncMock()
    service = AuditService(mock_repo)

    event = DomainEvent(
        event_type="USER_REGISTERED",
        source_agent="auth",
        payload={"email": "test@user.com", "status": "success"},
        correlation_id="corr_123"
    )

    await service.log_event(event)

    assert mock_repo.create.call_count == 1
    logged_model = mock_repo.create.call_args[0][0]
    assert logged_model.event_type == "USER_REGISTERED"
    assert logged_model.source == "auth"
    assert logged_model.action == "user_registered"
    assert logged_model.status == "success"
    assert logged_model.correlation_id == "corr_123"
    assert logged_model.payload["email"] == "test@user.com"
