import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from datetime import datetime, UTC

from app.domain.models.content import ContentModel
from app.domain.models.portfolio import PortfolioModel
from app.domain.models.networking import NetworkingModel
from app.domain.models.email import EmailModel
from app.domain.models.calendar import CalendarEventModel
from app.domain.models.interview import InterviewModel

from app.infrastructure.database.repositories.mongo_content_repo import MongoContentRepository
from app.infrastructure.database.repositories.mongo_portfolio_repo import MongoPortfolioRepository
from app.infrastructure.database.repositories.mongo_networking_repo import MongoNetworkingRepository
from app.infrastructure.database.repositories.mongo_email_repo import MongoEmailRepository
from app.infrastructure.database.repositories.mongo_calendar_repo import MongoCalendarRepository
from app.infrastructure.database.repositories.mongo_interview_repo import MongoInterviewRepository


@pytest.mark.asyncio
async def test_mongo_content_repo() -> None:
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = {
        "_id": ObjectId(),
        "platform": "linkedin",
        "title": "Post Title",
        "body": "Body Text",
        "status": "draft",
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }

    repo = MongoContentRepository(mock_collection)
    result = await repo.get_by_id("60c72b2f9b1d8e2b8c8b4567")
    assert result is not None
    assert result.platform == "linkedin"
    assert result.status == "draft"


@pytest.mark.asyncio
async def test_mongo_portfolio_repo() -> None:
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = {
        "_id": ObjectId(),
        "user_id": "user_123",
        "bio": "Developer bio",
        "skills": ["Python", "FastAPI"],
        "projects": [],
        "socials": {},
        "layout": {},
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC)
    }

    repo = MongoPortfolioRepository(mock_collection)
    result = await repo.get_by_user_id("user_123")
    assert result is not None
    assert result.user_id == "user_123"
    assert "Python" in result.skills


@pytest.mark.asyncio
async def test_mongo_networking_repo() -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.insert_one = AsyncMock()
    
    mock_cursor = MagicMock()
    async def mock_async_iterator(*args, **kwargs):
        yield {
            "_id": ObjectId(),
            "name": "Jane Doe",
            "role": "Recruiter",
            "company": "Google",
            "status": "identified"
        }
    mock_cursor.__aiter__ = mock_async_iterator
    mock_collection.find.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor
    
    repo = MongoNetworkingRepository(mock_collection)
    result = await repo.get_all()
    assert len(result) == 1
    assert result[0].name == "Jane Doe"


@pytest.mark.asyncio
async def test_mongo_email_repo() -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    
    mock_cursor = MagicMock()
    async def mock_async_iterator(*args, **kwargs):
        yield {
            "_id": ObjectId(),
            "thread_id": "thread_1",
            "to_email": "recruiter@google.com",
            "from_email": "user@example.com",
            "subject": "Reply",
            "body": "Body",
            "status": "draft",
            "type": "outbound"
        }
    mock_cursor.__aiter__ = mock_async_iterator
    mock_collection.find.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor

    repo = MongoEmailRepository(mock_collection)
    result = await repo.get_by_thread_id("thread_1")
    assert len(result) == 1
    assert result[0].to_email == "recruiter@google.com"


@pytest.mark.asyncio
async def test_mongo_calendar_repo() -> None:
    mock_collection = AsyncMock()
    mock_collection.find_one.return_value = {
        "_id": ObjectId(),
        "title": " recruiter call",
        "start_time": datetime.now(UTC),
        "end_time": datetime.now(UTC),
        "attendees": [],
        "status": "scheduled"
    }

    repo = MongoCalendarRepository(mock_collection)
    result = await repo.get_by_id("60c72b2f9b1d8e2b8c8b4567")
    assert result is not None
    assert result.status == "scheduled"


@pytest.mark.asyncio
async def test_mongo_interview_repo() -> None:
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    
    mock_cursor = MagicMock()
    async def mock_async_iterator(*args, **kwargs):
        yield {
            "_id": ObjectId(),
            "role": "Backend Engineer",
            "company": "Netflix",
            "questions": [],
            "status": "created"
        }
    mock_cursor.__aiter__ = mock_async_iterator
    mock_collection.find.return_value = mock_cursor
    mock_cursor.sort.return_value = mock_cursor

    repo = MongoInterviewRepository(mock_collection)
    result = await repo.get_by_job_id("job_abc")
    assert len(result) == 1
    assert result[0].company == "Netflix"
