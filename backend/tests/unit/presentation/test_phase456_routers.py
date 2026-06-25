import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import FastAPI
from fastapi.testclient import TestClient
from datetime import datetime, UTC

from app.presentation.api.v1.presence_router import router as presence_router
from app.presentation.api.v1.communication_router import router as communication_router
from app.presentation.api.v1.interview_router import router as interview_router
from app.application.dependencies.auth import get_current_user
from app.domain.models.content import ContentModel
from app.domain.models.portfolio import PortfolioModel
from app.domain.models.networking import NetworkingModel
from app.domain.models.email import EmailModel
from app.domain.models.calendar import CalendarEventModel
from app.domain.models.interview import InterviewModel
from app.agents.base.agent import AgentResult

router_test_app = FastAPI()
router_test_app.include_router(presence_router, prefix="/api/v1")
router_test_app.include_router(communication_router, prefix="/api/v1")
router_test_app.include_router(interview_router, prefix="/api/v1")

async def mock_get_current_user():
    return {"email": "test@example.com", "role": "admin", "id": "user_123"}

router_test_app.dependency_overrides[get_current_user] = mock_get_current_user

client = TestClient(router_test_app)


def test_get_content() -> None:
    mock_container = MagicMock()
    mock_content_repo = AsyncMock()
    mock_container.content_repo = mock_content_repo

    mock_content = MagicMock(spec=ContentModel)
    mock_content.model_dump.return_value = {"title": "LinkedIn post"}
    mock_content_repo.find.return_value = [mock_content]

    with patch("app.presentation.api.v1.presence_router.get_container", return_value=mock_container):
        response = client.get("/api/v1/presence/content?status=draft")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["contents"][0]["title"] == "LinkedIn post"


def test_approve_content() -> None:
    mock_container = MagicMock()
    mock_content_repo = AsyncMock()
    mock_event_bus = AsyncMock()
    mock_container.content_repo = mock_content_repo
    mock_container.event_bus = mock_event_bus

    mock_content = MagicMock(spec=ContentModel)
    mock_content.id = "content_1"
    mock_content.platform = "linkedin"
    mock_content_repo.get_by_id.return_value = mock_content

    with patch("app.presentation.api.v1.presence_router.get_container", return_value=mock_container):
        response = client.post("/api/v1/presence/content/content_1/approve")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_content_repo.update.assert_called_once()
        mock_event_bus.publish.assert_called_once()


def test_get_portfolio() -> None:
    mock_container = MagicMock()
    mock_user_repo = AsyncMock()
    mock_portfolio_repo = AsyncMock()
    mock_container.user_repo = mock_user_repo
    mock_container.portfolio_repo = mock_portfolio_repo

    mock_user = MagicMock()
    mock_user.id = "user_1"
    mock_user_repo.get_all.return_value = [mock_user]

    mock_portfolio = MagicMock(spec=PortfolioModel)
    mock_portfolio.model_dump.return_value = {"bio": "Hello World"}
    mock_portfolio_repo.get_by_user_id.return_value = mock_portfolio

    with patch("app.presentation.api.v1.presence_router.get_container", return_value=mock_container):
        response = client.get("/api/v1/presence/portfolio")
        assert response.status_code == 200
        data = response.json()
        assert data["bio"] == "Hello World"


def test_get_emails() -> None:
    mock_container = MagicMock()
    mock_email_repo = AsyncMock()
    mock_container.email_repo = mock_email_repo

    mock_email = MagicMock(spec=EmailModel)
    mock_email.model_dump.return_value = {"subject": "Hi"}
    mock_email_repo.find.return_value = [mock_email]

    with patch("app.presentation.api.v1.communication_router.get_container", return_value=mock_container):
        response = client.get("/api/v1/communication/emails?status=draft")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["emails"][0]["subject"] == "Hi"


def test_send_email_draft() -> None:
    mock_container = MagicMock()
    mock_email_repo = AsyncMock()
    mock_event_bus = AsyncMock()
    mock_container.email_repo = mock_email_repo
    mock_container.event_bus = mock_event_bus

    mock_email = MagicMock(spec=EmailModel)
    mock_email.id = "email_1"
    mock_email.to_email = "jane@example.com"
    mock_email.subject = "Follow up"
    mock_email.status = "draft"
    mock_email_repo.get_by_id.return_value = mock_email

    with patch("app.presentation.api.v1.communication_router.get_container", return_value=mock_container):
        response = client.post("/api/v1/communication/emails/email_1/send")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        mock_email_repo.update.assert_called_once()
        mock_event_bus.publish.assert_called_once()


def test_start_interview_session() -> None:
    mock_container = MagicMock()
    mock_orchestrator = MagicMock()
    mock_orchestrator.execute_agent = AsyncMock()
    mock_interview_agent = MagicMock()
    mock_container.orchestrator = mock_orchestrator
    mock_orchestrator.registry.get.return_value = mock_interview_agent
    
    mock_orchestrator.execute_agent.return_value = AgentResult(
        success=True,
        data={"interview_id": "session_abc"},
        message="Created"
    )

    with patch("app.presentation.api.v1.interview_router.get_container", return_value=mock_container):
        response = client.post("/api/v1/interview/sessions?job_id=job_123")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["interview_id"] == "session_abc"


def test_answer_interview_question() -> None:
    mock_container = MagicMock()
    mock_interview_repo = AsyncMock()
    mock_llm_service = AsyncMock()
    mock_container.interview_repo = mock_interview_repo
    mock_container.llm_service = mock_llm_service

    mock_session = MagicMock(spec=InterviewModel)
    mock_session.id = "session_1"
    mock_session.questions = [
        {"question": "Q1", "ideal_answer": "Ideal", "user_answer": "", "score": None}
    ]
    mock_session.to_dict.return_value = {}
    mock_interview_repo.get_by_id.return_value = mock_session

    mock_llm_service.evaluate_interview_answer.return_value = {
        "score": 90.0,
        "feedback": "Great",
        "strengths": [],
        "improvements": []
    }

    with patch("app.presentation.api.v1.interview_router.get_container", return_value=mock_container):
        response = client.post("/api/v1/interview/sessions/session_1/answer?question_index=0", json="My Answer")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["score"] == 90.0
        mock_interview_repo.update.assert_called_once()
