import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId

from app.domain.models.application import ApplicationModel
from app.domain.models.digest import DigestModel
from app.domain.models.learning_plan import LearningPlanModel
from app.domain.models.knowledge import KnowledgeModel
from app.infrastructure.database.repositories.mongo_application_repo import MongoApplicationRepository
from app.infrastructure.database.repositories.mongo_digest_repo import MongoDigestRepository
from app.infrastructure.database.repositories.mongo_learning_plan_repo import MongoLearningPlanRepository
from app.infrastructure.database.repositories.mongo_knowledge_repo import MongoKnowledgeRepository


@pytest.mark.asyncio
async def test_mongo_application_repo() -> None:
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = {
        "_id": ObjectId(),
        "user_id": "user_1",
        "job_id": "job_1",
        "match_score": {"overall": 80.0},
        "status": "pending_approval",
        "created_at": "2026-06-25T11:00:00",
        "updated_at": "2026-06-25T11:00:00"
    }

    repo = MongoApplicationRepository(mock_collection)
    result = await repo.get_by_user_and_job("user_1", "job_1")
    assert result is not None
    assert result.user_id == "user_1"
    assert result.match_score.overall == 80.0


@pytest.mark.asyncio
async def test_mongo_digest_repo() -> None:
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = {
        "_id": ObjectId(),
        "title": "Digest Title",
        "type": "daily",
        "summary": "Summary",
        "created_at": "2026-06-25T11:00:00"
    }

    repo = MongoDigestRepository(mock_collection)
    result = await repo.get_latest_by_type("daily")
    assert result is not None
    assert result.title == "Digest Title"


@pytest.mark.asyncio
async def test_mongo_learning_plan_repo() -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.insert_one = AsyncMock()
    mock_collection.update_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    
    mock_cursor = MagicMock()
    
    async def mock_async_iterator(*args, **kwargs):
        yield {
            "_id": ObjectId(),
            "user_id": "user_1",
            "title": "Learn FastAPI",
            "target_skills": ["FastAPI"],
            "tasks": [],
            "status": "in_progress",
            "created_at": "2026-06-25T11:00:00",
            "updated_at": "2026-06-25T11:00:00"
        }
        
    mock_cursor.__aiter__ = mock_async_iterator
    mock_collection.find.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor

    repo = MongoLearningPlanRepository(mock_collection)
    result = await repo.get_by_user_id("user_1")
    assert len(result) == 1
    assert result[0].title == "Learn FastAPI"


@pytest.mark.asyncio
async def test_mongo_knowledge_repo() -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.insert_one = AsyncMock()
    mock_collection.update_one = AsyncMock()
    mock_collection.delete_one = AsyncMock()
    
    mock_cursor = MagicMock()
    
    async def mock_async_iterator(*args, **kwargs):
        yield {
            "_id": ObjectId(),
            "title": "Knowledge Title",
            "type": "paper",
            "summary": "Summary",
            "url": "http://arxiv.org",
            "metadata": {},
            "created_at": "2026-06-25T11:00:00"
        }
        
    mock_cursor.__aiter__ = mock_async_iterator
    mock_collection.find.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor

    repo = MongoKnowledgeRepository(mock_collection)
    result = await repo.get_by_type("paper")
    assert len(result) == 1
    assert result[0].title == "Knowledge Title"

