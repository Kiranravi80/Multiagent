import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.job_classifier_agent import JobClassifierAgent
from app.agents.jb_analyzer_agent import JDAnalyzerAgent
from app.agents.job_matcher_agent import JobMatcherAgent
from app.domain.models.job import JobModel
from app.core.constants import JobStatus


@pytest.mark.asyncio
async def test_job_classifier_agent() -> None:
    mock_bus = AsyncMock()
    mock_repo = AsyncMock()
    
    mock_job = MagicMock(spec=JobModel)
    mock_job.id = "job_1"
    mock_job.title = "Software Engineer"
    mock_job.company = "Google"
    mock_job.description = "We are looking for a Python developer..."
    mock_job.skills = []
    
    mock_repo.find.return_value = [mock_job]

    # Mock container and LLMService
    mock_llm = AsyncMock()
    mock_llm.classify_job.return_value = {
        "is_relevant": True,
        "category": "backend",
        "subcategory": "python",
        "confidence": 0.95
    }
    
    mock_container = MagicMock()
    mock_container.llm_service = mock_llm

    with patch("app.application.dependencies.container.get_container", return_value=mock_container):
        agent = JobClassifierAgent(event_bus=mock_bus, job_repo=mock_repo)
        await agent.initialize()
        
        result = await agent.execute()
        
        assert result.success is True
        assert result.data["classified_count"] == 1
        assert result.data["relevant_count"] == 1
        
        mock_repo.update.assert_called_once()
        mock_bus.publish.assert_called_once()


@pytest.mark.asyncio
async def test_jd_analyzer_agent() -> None:
    mock_bus = AsyncMock()
    mock_repo = AsyncMock()
    
    mock_job = MagicMock(spec=JobModel)
    mock_job.id = "job_2"
    mock_job.description = "Requirements: Python, AWS, Docker."
    
    mock_repo.find.return_value = [mock_job]

    mock_llm = AsyncMock()
    mock_llm.analyze_jd.return_value = {
        "required_skills": ["Python", "AWS", "Docker"],
        "preferred_skills": [],
        "work_type": "remote"
    }
    
    mock_container = MagicMock()
    mock_container.llm_service = mock_llm

    with patch("app.application.dependencies.container.get_container", return_value=mock_container):
        agent = JDAnalyzerAgent(event_bus=mock_bus, job_repo=mock_repo)
        await agent.initialize()
        
        result = await agent.execute()
        
        assert result.success is True
        assert result.data["analyzed_count"] == 1
        mock_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_job_matcher_agent() -> None:
    mock_bus = AsyncMock()
    mock_repo = AsyncMock()
    mock_user_repo = AsyncMock()
    mock_app_repo = AsyncMock()
    
    mock_user = MagicMock()
    mock_user.id = "user_1"
    mock_user.skills = ["Python"]
    mock_user.experience = []
    mock_user.education = []
    mock_user.projects = []
    mock_user.preferences = None
    mock_user.career_analysis = None
    mock_user_repo.get_all.return_value = [mock_user]

    mock_job = MagicMock(spec=JobModel)
    mock_job.id = "job_3"
    mock_job.jd_analysis = None
    mock_repo.find.return_value = [mock_job]

    mock_llm = AsyncMock()
    mock_llm.match_job.return_value = {
        "overall": 85.0,
        "skill": 90.0,
        "experience": 80.0
    }
    
    mock_container = MagicMock()
    mock_container.llm_service = mock_llm
    mock_app_repo.get_by_user_and_job.return_value = None

    with patch("app.application.dependencies.container.get_container", return_value=mock_container):
        agent = JobMatcherAgent(
            event_bus=mock_bus,
            job_repo=mock_repo,
            user_repo=mock_user_repo,
            application_repo=mock_app_repo
        )
        
        result = await agent.execute()
        
        assert result.success is True
        assert result.data["matched_count"] == 1
        mock_app_repo.create.assert_called_once()
