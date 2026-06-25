import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.application.services.metrics_service import MetricsService


@pytest.mark.asyncio
async def test_metrics_service_gathering() -> None:
    # Setup mocks
    mock_container = MagicMock()
    mock_container.orchestrator.get_all_health = AsyncMock(return_value={
        "agent_1": {"healthy": True, "status": "idle"},
        "agent_2": {"healthy": False, "status": "error"}
    })
    mock_container.db_manager.health_check = AsyncMock(return_value=True)
    mock_container.db_manager.get_database.return_value.command = AsyncMock()
    mock_container.job_repo.count = AsyncMock(return_value=42)
    mock_container.user_repo.count = AsyncMock(return_value=2)
    mock_container.resume_repo.count = AsyncMock(return_value=5)
    mock_container.audit_repo.count = AsyncMock(return_value=100)

    with patch("app.application.dependencies.container.get_container", return_value=mock_container):
        service = MetricsService()
        stats = await service.get_system_metrics()

        assert stats["agents"]["total"] == 2
        assert stats["agents"]["healthy"] == 1
        assert stats["agents"]["unhealthy"] == 1
        assert stats["database"]["connected"] is True
        assert stats["database"]["collections"]["jobs"] == 42
        assert stats["database"]["collections"]["users"] == 2
        assert stats["database"]["collections"]["resumes"] == 5
        assert stats["database"]["collections"]["audit_logs"] == 100
