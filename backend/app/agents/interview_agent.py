"""Interview Agent.

Generates targeted mock interview questions and evaluates user answers.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.agents.base.agent import AgentResult, BaseAgent
from app.core.constants import EventType
from app.domain.events.base import DomainEvent
from app.domain.models.interview import InterviewModel
from app.domain.repositories.interview_repository import InterviewRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.resume_repository import ResumeRepository


class InterviewAgent(BaseAgent):
    """AI agent that generates customized mock interviews and grades responses."""

    def __init__(
        self,
        *,
        event_bus: Any,
        interview_repo: InterviewRepository,
        job_repo: JobRepository,
        resume_repo: ResumeRepository,
    ) -> None:
        super().__init__(name="interview_agent", event_bus=event_bus)
        self._interview_repo = interview_repo
        self._job_repo = job_repo
        self._resume_repo = resume_repo

    async def initialize(self) -> None:
        """Subscribe to application approved events."""
        await self.subscribe(EventType.APPLICATION_APPROVED, self.on_trigger_event)
        self._logger.info("interview_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Generate targeted mock interview prep session."""
        self._logger.info("interview_agent_run_started")

        job_id = context.get("job_id") if context else None
        if not job_id:
            # Fallback to latest job in database
            jobs = await self._job_repo.get_all(limit=1)
            if not jobs:
                return AgentResult(success=False, data={}, message="No jobs available to generate mock interview for.")
            job_id = jobs[0].id

        job = await self._job_repo.get_by_id(job_id)
        if not job:
            return AgentResult(success=False, data={}, message=f"Job {job_id} not found.")

        # Find user resume
        resumes = await self._resume_repo.get_all(limit=1)
        resume_text = resumes[0].raw_text if resumes else "Python Backend Developer, FastAPI, MongoDB, Docker."

        # Import LLMService lazily
        from app.application.dependencies.container import get_container
        llm_service = get_container().llm_service

        try:
            # Generate Q&A set via LLM
            qa_data = await llm_service.generate_interview_questions(
                role=job.title,
                company=job.company,
                resume_text=resume_text,
                jd_text=job.description
            )

            # Create mock session
            questions = [
                {
                    "question": q["question"],
                    "type": q["type"],
                    "ideal_answer": q["ideal_answer"],
                    "user_answer": "",
                    "score": None,
                    "feedback": ""
                }
                for q in qa_data.get("questions", [])
            ]

            session = InterviewModel(
                job_id=job.id,
                role=job.title,
                company=job.company,
                questions=questions,
                status="created"
            )
            session_id = await self._interview_repo.create(session)

            return AgentResult(
                success=True,
                data={"interview_id": session_id},
                message=f"Mock interview prep session created with {len(questions)} questions."
            )

        except Exception as exc:
            self._logger.error("interview_generation_failed", error=str(exc))
            return AgentResult(success=False, data={}, message=f"Failed to generate mock interview: {exc}")

    async def on_trigger_event(self, event: Any) -> None:
        """Asynchronously trigger agent execute on event receipt."""
        self._logger.info("interview_trigger_received", event_type=event.event_type)
        context = {}
        if event.payload and "job_id" in event.payload:
            context["job_id"] = event.payload["job_id"]
        asyncio.create_task(self.execute(context))
