import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId

from app.domain.models.agent_state import AgentStateModel
from app.infrastructure.database.repositories.mongo_agent_state_repo import MongoAgentStateRepository


@pytest.mark.asyncio
async def test_mongo_agent_state_repo_get_by_name() -> None:
    mock_collection = AsyncMock()
    mock_doc = {
        "_id": ObjectId(),
        "agent_name": "test_agent",
        "status": "idle",
        "state_data": {},
        "metrics": {
            "total_executions": 5,
            "successful_executions": 5,
            "failed_executions": 0,
            "avg_duration_seconds": 1.2,
            "last_duration_seconds": 1.0,
        }
    }
    mock_collection.find_one.return_value = mock_doc

    repo = MongoAgentStateRepository(mock_collection)
    result = await repo.get_by_name("test_agent")

    assert result is not None
    assert result.agent_name == "test_agent"
    assert result.metrics.total_executions == 5
    mock_collection.find_one.assert_called_once_with({"agent_name": "test_agent"})
