import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from bson import ObjectId

from app.presentation.api.v1.application_router import router as application_router
from app.presentation.api.v1.knowledge_router import router as knowledge_router
from app.application.dependencies.auth import get_current_user
from app.domain.models.application import ApplicationModel
from app.domain.models.digest import DigestModel
from app.domain.models.learning_plan import LearningPlanModel
from app.domain.models.knowledge import KnowledgeModel
from app.domain.models.job import JobModel
from app.core.constants import ApplicationStatus

# Setup test app without database lifespan side-effects
router_test_app = FastAPI()
router_test_app.include_router(application_router, prefix="/api/v1")
router_test_app.include_router(knowledge_router, prefix="/api/v1")

# Mock authentication dependency
async def mock_get_current_user():
    return {"email": "test@example.com", "role": "admin", "id": "user_123"}

router_test_app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(router_test_app)


def test_get_applications() -> None:
    mock_container = MagicMock()
    mock_app_repo = AsyncMock()
    mock_job_repo = AsyncMock()
    mock_container.application_repo = mock_app_repo
    mock_container.job_repo = mock_job_repo

    # Mock application
    mock_app = MagicMock(spec=ApplicationModel)
    mock_app.id = "app_1"
    mock_app.job_id = "job_1"
    mock_app.user_id = "user_1"
    mock_app.status = ApplicationStatus.PENDING_APPROVAL
    mock_app.model_dump.return_value = {
        "id": "app_1",
        "job_id": "job_1",
        "user_id": "user_1",
        "status": "pending_approval",
        "match_score": {"overall": 85.0}
    }
    mock_app_repo.find.return_value = [mock_app]

    # Mock job
    mock_job = MagicMock(spec=JobModel)
    mock_job.title = "Software Engineer"
    mock_job.company = "Google"
    mock_job.location = "Mountain View"
    mock_job.source = "LinkedIn"
    mock_job_repo.get_by_id.return_value = mock_job

    with patch("app.presentation.api.v1.application_router.get_container", return_value=mock_container):
        response = client.get("/api/v1/applications?status=pending_approval")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["applications"][0]["job_title"] == "Software Engineer"
        assert data["applications"][0]["company"] == "Google"
        mock_app_repo.find.assert_called_once_with({"status": "pending_approval"})


def test_get_application_details() -> None:
    mock_container = MagicMock()
    mock_app_repo = AsyncMock()
    mock_job_repo = AsyncMock()
    mock_container.application_repo = mock_app_repo
    mock_container.job_repo = mock_job_repo

    mock_app = MagicMock(spec=ApplicationModel)
    mock_app.id = "app_1"
    mock_app.job_id = "job_1"
    mock_app.model_dump.return_value = {
        "id": "app_1",
        "job_id": "job_1",
        "status": "pending_approval"
    }
    mock_app_repo.get_by_id.return_value = mock_app

    mock_job = MagicMock(spec=JobModel)
    mock_job.model_dump.return_value = {
        "title": "Software Engineer",
        "company": "Google"
    }
    mock_job_repo.get_by_id.return_value = mock_job

    with patch("app.presentation.api.v1.application_router.get_container", return_value=mock_container):
        response = client.get("/api/v1/applications/app_1")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "app_1"
        assert data["job"]["title"] == "Software Engineer"


def test_approve_application() -> None:
    mock_container = MagicMock()
    mock_app_repo = AsyncMock()
    mock_event_bus = AsyncMock()
    mock_container.application_repo = mock_app_repo
    mock_container.event_bus = mock_event_bus

    mock_app = MagicMock(spec=ApplicationModel)
    mock_app.id = "app_1"
    mock_app.job_id = "job_1"
    mock_app.status = ApplicationStatus.PENDING_APPROVAL
    mock_app_repo.get_by_id.return_value = mock_app

    with patch("app.presentation.api.v1.application_router.get_container", return_value=mock_container):
        response = client.post("/api/v1/applications/app_1/approve")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_app.transition_status.assert_called_once_with(
            ApplicationStatus.APPROVED,
            notes="Approved by user test@example.com"
        )
        mock_app_repo.update.assert_called_once()
        mock_event_bus.publish.assert_called_once()


def test_get_digests() -> None:
    mock_container = MagicMock()
    mock_digest_repo = AsyncMock()
    mock_container.digest_repo = mock_digest_repo

    mock_digest = MagicMock(spec=DigestModel)
    mock_digest.model_dump.return_value = {
        "title": "Daily AI Digest",
        "type": "daily"
    }
    mock_digest_repo.find.return_value = [mock_digest]

    with patch("app.presentation.api.v1.knowledge_router.get_container", return_value=mock_container):
        response = client.get("/api/v1/knowledge/digests?digest_type=daily")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["digests"][0]["title"] == "Daily AI Digest"


def test_get_latest_digest() -> None:
    mock_container = MagicMock()
    mock_digest_repo = AsyncMock()
    mock_container.digest_repo = mock_digest_repo

    mock_digest = MagicMock(spec=DigestModel)
    mock_digest.model_dump.return_value = {
        "title": "Weekly Report",
        "type": "weekly"
    }
    mock_digest_repo.get_latest_by_type.return_value = mock_digest

    with patch("app.presentation.api.v1.knowledge_router.get_container", return_value=mock_container):
        response = client.get("/api/v1/knowledge/digests/latest?digest_type=weekly")
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Weekly Report"


def test_get_learning_plans() -> None:
    mock_container = MagicMock()
    mock_user_repo = AsyncMock()
    mock_learning_plan_repo = AsyncMock()
    mock_container.user_repo = mock_user_repo
    mock_container.learning_plan_repo = mock_learning_plan_repo

    mock_user = MagicMock()
    mock_user.id = "user_1"
    mock_user_repo.get_all.return_value = [mock_user]

    mock_plan = MagicMock(spec=LearningPlanModel)
    mock_plan.model_dump.return_value = {
        "title": "System Design Study Plan"
    }
    mock_learning_plan_repo.get_by_user_id.return_value = [mock_plan]

    with patch("app.presentation.api.v1.knowledge_router.get_container", return_value=mock_container):
        response = client.get("/api/v1/knowledge/learning-plans")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["learning_plans"][0]["title"] == "System Design Study Plan"


def test_get_knowledge_items() -> None:
    mock_container = MagicMock()
    mock_knowledge_repo = AsyncMock()
    mock_container.knowledge_repo = mock_knowledge_repo

    mock_item = MagicMock(spec=KnowledgeModel)
    mock_item.model_dump.return_value = {
        "title": "Attention is All You Need",
        "type": "paper"
    }
    mock_knowledge_repo.find.return_value = [mock_item]

    with patch("app.presentation.api.v1.knowledge_router.get_container", return_value=mock_container):
        response = client.get("/api/v1/knowledge/items?item_type=paper")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["items"][0]["title"] == "Attention is All You Need"
