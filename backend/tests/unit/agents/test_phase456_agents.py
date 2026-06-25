import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId

from app.agents.linkedin_content_agent import LinkedInContentAgent
from app.agents.portfolio_agent import PortfolioAgent
from app.agents.github_agent import GitHubAgent
from app.agents.networking_agent import NetworkingAgent
from app.agents.outreach_manager import OutreachManager
from app.agents.email_agent import EmailAgent
from app.agents.calendar_agent import CalendarAgent
from app.agents.interview_agent import InterviewAgent

from app.domain.models.user import UserModel
from app.domain.models.job import JobModel
from app.domain.models.application import ApplicationModel
from app.domain.models.content import ContentModel
from app.domain.models.portfolio import PortfolioModel
from app.domain.models.networking import NetworkingModel
from app.domain.models.email import EmailModel
from app.domain.models.calendar import CalendarEventModel
from app.domain.models.interview import InterviewModel


@pytest.mark.asyncio
async def test_linkedin_content_agent() -> None:
    mock_bus = AsyncMock()
    mock_content_repo = AsyncMock()
    mock_user_repo = AsyncMock()

    mock_user = MagicMock(spec=UserModel)
    mock_user.id = "user_1"
    mock_user.bio = "Backend Dev"
    mock_user.skills = ["Python"]
    mock_user_repo.get_all.return_value = [mock_user]

    mock_llm = AsyncMock()
    mock_llm.generate_content.return_value = {
        "title": "A tech hook",
        "body": "Post content"
    }

    mock_container = MagicMock()
    mock_container.llm_service = mock_llm

    with patch("app.application.dependencies.container.get_container", return_value=mock_container):
        agent = LinkedInContentAgent(
            event_bus=mock_bus,
            content_repo=mock_content_repo,
            user_repo=mock_user_repo
        )
        await agent.initialize()
        result = await agent.execute()

        assert result.success is True
        mock_content_repo.create.assert_called_once()
        mock_bus.publish.assert_called_once()


@pytest.mark.asyncio
async def test_portfolio_agent() -> None:
    mock_bus = AsyncMock()
    mock_portfolio_repo = AsyncMock()
    mock_user_repo = AsyncMock()

    mock_user = MagicMock(spec=UserModel)
    mock_user.id = "user_1"
    mock_user.skills = ["Python"]
    mock_user.experience = []
    mock_user.education = []
    mock_user_repo.get_all.return_value = [mock_user]
    mock_portfolio_repo.get_by_user_id.return_value = None

    mock_llm = AsyncMock()
    mock_llm.generate_portfolio_config.return_value = {
        "bio": "website bio",
        "skills": ["Python"],
        "projects": [],
        "layout": {}
    }

    mock_container = MagicMock()
    mock_container.llm_service = mock_llm

    with patch("app.application.dependencies.container.get_container", return_value=mock_container):
        agent = PortfolioAgent(
            event_bus=mock_bus,
            portfolio_repo=mock_portfolio_repo,
            user_repo=mock_user_repo
        )
        await agent.initialize()
        result = await agent.execute()

        assert result.success is True
        mock_portfolio_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_github_agent() -> None:
    mock_bus = AsyncMock()
    mock_content_repo = AsyncMock()
    mock_user_repo = AsyncMock()

    mock_user = MagicMock(spec=UserModel)
    mock_user.id = "user_1"
    mock_user.skills = ["Python"]
    mock_user.projects = []
    mock_user_repo.get_all.return_value = [mock_user]

    mock_llm = AsyncMock()
    mock_llm.generate_content.return_value = {
        "title": "README",
        "body": "body"
    }

    mock_container = MagicMock()
    mock_container.llm_service = mock_llm

    with patch("app.application.dependencies.container.get_container", return_value=mock_container):
        agent = GitHubAgent(
            event_bus=mock_bus,
            content_repo=mock_content_repo,
            user_repo=mock_user_repo
        )
        await agent.initialize()
        result = await agent.execute()

        assert result.success is True
        mock_content_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_networking_agent() -> None:
    mock_bus = AsyncMock()
    mock_networking_repo = AsyncMock()
    mock_job_repo = AsyncMock()

    mock_job = MagicMock(spec=JobModel)
    mock_job.id = "job_1"
    mock_job.company = "Google"
    mock_job.title = "SWE"
    mock_job_repo.get_by_id.return_value = mock_job

    mock_app = MagicMock(spec=ApplicationModel)
    mock_app.job_id = "job_1"

    mock_app_repo = AsyncMock()
    mock_app_repo.get_all.return_value = [mock_app]

    mock_networking_repo.find.return_value = []

    mock_container = MagicMock()
    mock_container.application_repo = mock_app_repo

    with patch("app.application.dependencies.container.get_container", return_value=mock_container):
        agent = NetworkingAgent(
            event_bus=mock_bus,
            networking_repo=mock_networking_repo,
            job_repo=mock_job_repo
        )
        await agent.initialize()
        result = await agent.execute()

        assert result.success is True
        assert mock_networking_repo.create.call_count == 2


@pytest.mark.asyncio
async def test_outreach_manager() -> None:
    mock_bus = AsyncMock()
    mock_networking_repo = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_email_repo = AsyncMock()

    mock_contact = MagicMock(spec=NetworkingModel)
    mock_contact.id = "contact_1"
    mock_contact.name = "Jane"
    mock_contact.role = "Recruiter"
    mock_contact.company = "Google"
    mock_contact.email = "jane@google.com"
    mock_contact.interaction_history = []
    mock_networking_repo.find.return_value = [mock_contact]
    mock_networking_repo.get_by_id.return_value = mock_contact

    mock_user = MagicMock(spec=UserModel)
    mock_user.email = "user@example.com"
    mock_user_repo.get_all.return_value = [mock_user]

    mock_llm = AsyncMock()
    mock_llm.draft_outreach.return_value = {
        "subject": "Hi",
        "message": "Let's connect"
    }

    mock_container = MagicMock()
    mock_container.llm_service = mock_llm

    with patch("app.application.dependencies.container.get_container", return_value=mock_container):
        agent = OutreachManager(
            event_bus=mock_bus,
            networking_repo=mock_networking_repo,
            user_repo=mock_user_repo,
            email_repo=mock_email_repo
        )
        await agent.initialize()
        result = await agent.execute()

        assert result.success is True
        mock_networking_repo.update.assert_called_once()
        mock_email_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_email_agent() -> None:
    mock_bus = AsyncMock()
    mock_email_repo = AsyncMock()
    mock_user_repo = AsyncMock()

    mock_email = MagicMock(spec=EmailModel)
    mock_email.id = "email_1"
    mock_email.thread_id = "thread_1"
    mock_email.from_email = "recruiter@google.com"
    mock_email.subject = "Invite"
    mock_email.body = "Hey"
    mock_email_repo.find.side_effect = [[mock_email], []]
    mock_email_repo.get_by_id.return_value = mock_email

    mock_user = MagicMock(spec=UserModel)
    mock_user.email = "user@example.com"
    mock_user_repo.get_all.return_value = [mock_user]

    mock_llm = AsyncMock()
    mock_llm.draft_email_reply.return_value = {
        "subject": "Re: Invite",
        "body": "Thanks"
    }

    mock_container = MagicMock()
    mock_container.llm_service = mock_llm

    with patch("app.application.dependencies.container.get_container", return_value=mock_container):
        agent = EmailAgent(
            event_bus=mock_bus,
            email_repo=mock_email_repo,
            user_repo=mock_user_repo
        )
        await agent.initialize()
        result = await agent.execute()

        assert result.success is True
        mock_email_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_calendar_agent() -> None:
    mock_bus = AsyncMock()
    mock_calendar_repo = AsyncMock()
    mock_email_repo = AsyncMock()

    mock_email = MagicMock(spec=EmailModel)
    mock_email.id = "email_1"
    mock_email.thread_id = "thread_1"
    mock_email.from_email = "recruiter@google.com"
    mock_email.to_email = "user@example.com"
    mock_email.body = "Let's schedule an interview next week."
    mock_email_repo.find.return_value = [mock_email]
    mock_email_repo.get_by_id.return_value = mock_email

    agent = CalendarAgent(
        event_bus=mock_bus,
        calendar_repo=mock_calendar_repo,
        email_repo=mock_email_repo
    )
    await agent.initialize()
    result = await agent.execute()

    assert result.success is True
    mock_calendar_repo.create.assert_called_once()
    mock_bus.publish.assert_called_once()


@pytest.mark.asyncio
async def test_interview_agent() -> None:
    mock_bus = AsyncMock()
    mock_interview_repo = AsyncMock()
    mock_job_repo = AsyncMock()
    mock_resume_repo = AsyncMock()

    mock_job = MagicMock(spec=JobModel)
    mock_job.id = "job_1"
    mock_job.title = "SWE"
    mock_job.company = "Google"
    mock_job.description = "Requirements"
    mock_job_repo.get_all.return_value = [mock_job]
    mock_job_repo.get_by_id.return_value = mock_job

    mock_resume_repo.get_all.return_value = []

    mock_llm = AsyncMock()
    mock_llm.generate_interview_questions.return_value = {
        "questions": [
            {
                "question": "What is Python?",
                "type": "technical",
                "ideal_answer": "An interpreted language"
            }
        ]
    }

    mock_container = MagicMock()
    mock_container.llm_service = mock_llm

    with patch("app.application.dependencies.container.get_container", return_value=mock_container):
        agent = InterviewAgent(
            event_bus=mock_bus,
            interview_repo=mock_interview_repo,
            job_repo=mock_job_repo,
            resume_repo=mock_resume_repo
        )
        await agent.initialize()
        result = await agent.execute()

        assert result.success is True
        mock_interview_repo.create.assert_called_once()
