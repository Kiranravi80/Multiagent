"""JD Analyzer Agent.

Extracts structured requirements and skills from job descriptions.
"""

from __future__ import annotations

from typing import Any

from app.agents.base.agent import BaseAgent, AgentResult
from app.core.constants import EventType, JobStatus
from app.domain.events.career_events import jd_analyzed_event
from app.domain.repositories.job_repository import JobRepository


class JDAnalyzerAgent(BaseAgent):
    """AI agent that processes job descriptions into structured constraints."""

    def __init__(self, *, event_bus: Any, job_repo: JobRepository) -> None:
        super().__init__(name="jd_analyzer_agent", event_bus=event_bus)
        self._job_repo = job_repo

    async def initialize(self) -> None:
        """Subscribe to job classification triggers."""
        await self.subscribe(EventType.JOB_CLASSIFIED, self.on_job_classified)
        self._logger.info("jd_analyzer_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Manual trigger: Analyze all CLASSIFIED jobs in the database."""
        self._logger.info("jd_analysis_run_started")

        classified_jobs = await self._job_repo.find({"status": JobStatus.CLASSIFIED})
        if not classified_jobs:
            return AgentResult(success=True, data={"analyzed_count": 0}, message="No classified jobs to analyze.")

        analyzed_count = 0

        # Import LLMService lazily from DI container
        from app.application.dependencies.container import get_container
        llm_service = get_container().llm_service

        for job in classified_jobs:
            try:
                # Deep description analysis
                analysis_data = await llm_service.analyze_jd(job.description)
                
                # Update job record
                update_data: dict[str, Any] = {
                    "status": JobStatus.ANALYZED,
                    "jd_analysis": analysis_data
                }
                await self._job_repo.update(job.id, update_data)
                
                # Publish event
                event = jd_analyzed_event(
                    source=self.name,
                    job_id=job.id,
                    analysis=analysis_data,
                )
                await self.publish_event(event)

                analyzed_count += 1
            except Exception as exc:
                self._logger.error("jd_analysis_failed", job_id=job.id, error=str(exc))

        return AgentResult(
            success=True,
            data={"analyzed_count": analyzed_count},
            message=f"Successfully analyzed {analyzed_count} job descriptions."
        )

    async def on_job_classified(self, event: Any) -> None:
        """Triggered automatically via pub/sub when a job is classified."""
        # Only analyze if the job classification is relevant
        is_relevant = event.payload.get("is_relevant", False)
        if not is_relevant:
            return

        self._logger.info("jd_analyzer_event_received", event_type=event.event_type)
        import asyncio
        asyncio.create_task(self.execute())
