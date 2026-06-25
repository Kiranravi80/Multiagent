"""Job Classifier Agent.

Processes new jobs, determines relevance using LLM, and transitions pipeline state.
"""

from __future__ import annotations

from typing import Any

from app.agents.base.agent import BaseAgent, AgentResult
from app.core.constants import EventType, JobStatus
from app.domain.events.career_events import job_classified_event
from app.domain.repositories.job_repository import JobRepository


class JobClassifierAgent(BaseAgent):
    """AI agent that determines if raw job listings are relevant tech positions."""

    def __init__(self, *, event_bus: Any, job_repo: JobRepository) -> None:
        super().__init__(name="job_classifier_agent", event_bus=event_bus)
        self._job_repo = job_repo

    async def initialize(self) -> None:
        """Subscribe to job collection trigger events."""
        await self.subscribe(EventType.JOB_COLLECTED, self.on_jobs_collected)
        self._logger.info("job_classifier_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Manual trigger: Classify all NEW jobs in the database."""
        self._logger.info("job_classification_run_started")
        
        new_jobs = await self._job_repo.find({"status": JobStatus.NEW})
        if not new_jobs:
            return AgentResult(success=True, data={"classified_count": 0}, message="No new jobs to classify.")

        classified_count = 0
        relevant_count = 0

        # Import LLMService lazily from DI container
        from app.application.dependencies.container import get_container
        llm_service = get_container().llm_service

        for job in new_jobs:
            try:
                # Classify via LLM
                classification_data = await llm_service.classify_job({
                    "title": job.title,
                    "company": job.company,
                    "description": job.description,
                    "skills": job.skills,
                })
                
                is_relevant = classification_data.get("is_relevant", False)
                
                # Update job record
                update_data: dict[str, Any] = {
                    "status": JobStatus.CLASSIFIED if is_relevant else JobStatus.ARCHIVED,
                    "classification": classification_data
                }
                await self._job_repo.update(job.id, update_data)
                
                # Publish event
                event = job_classified_event(
                    source=self.name,
                    job_id=job.id,
                    is_relevant=is_relevant,
                    category=classification_data.get("category", "other"),
                    confidence=classification_data.get("confidence", 0.0),
                )
                await self.publish_event(event)

                classified_count += 1
                if is_relevant:
                    relevant_count += 1
                    
            except Exception as exc:
                self._logger.error("job_classification_failed", job_id=job.id, error=str(exc))

        return AgentResult(
            success=True,
            data={"classified_count": classified_count, "relevant_count": relevant_count},
            message=f"Classified {classified_count} jobs. Found {relevant_count} relevant positions."
        )

    async def on_jobs_collected(self, event: Any) -> None:
        """Triggered automatically via pub/sub when jobs are collected."""
        self._logger.info("job_classifier_event_received", event_type=event.event_type)
        # Run execution asynchronously in background
        import asyncio
        asyncio.create_task(self.execute())
