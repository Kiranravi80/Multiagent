"""Job Matcher Agent.

Matches job descriptions against user profiles, generating match scores and initializing applications.
"""

from __future__ import annotations

from typing import Any

from app.agents.base.agent import BaseAgent, AgentResult
from app.core.constants import ApplicationStatus, EventType, JobStatus
from app.domain.events.career_events import job_matched_event
from app.domain.models.application import ApplicationModel, MatchScore
from app.domain.repositories.application_repository import ApplicationRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.user_repository import UserRepository


class JobMatcherAgent(BaseAgent):
    """AI agent that evaluates job descriptions against the user profile."""

    def __init__(
        self,
        *,
        event_bus: Any,
        job_repo: JobRepository,
        user_repo: UserRepository,
        application_repo: ApplicationRepository,
    ) -> None:
        super().__init__(name="job_matcher_agent", event_bus=event_bus)
        self._job_repo = job_repo
        self._user_repo = user_repo
        self._application_repo = application_repo

    async def initialize(self) -> None:
        """Subscribe to job description analysis completion events."""
        await self.subscribe(EventType.JD_ANALYZED, self.on_jd_analyzed)
        self._logger.info("job_matcher_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Manual trigger: Match all ANALYZED jobs in the database against the user profile."""
        self._logger.info("job_matching_run_started")

        # 1. Get primary user (first user registered in PAIOS)
        users = await self._user_repo.get_all(limit=1)
        if not users:
            return AgentResult(success=False, data={}, message="No user registered in PAIOS. Job matching skipped.")
        user = users[0]

        analyzed_jobs = await self._job_repo.find({"status": JobStatus.ANALYZED})
        if not analyzed_jobs:
            return AgentResult(success=True, data={"matched_count": 0}, message="No analyzed jobs to match.")

        # Prepare user profile dictionary for LLM matching
        profile_data = {
            "skills": user.skills,
            "experience": [e.model_dump() for e in user.experience],
            "education": [ed.model_dump() for ed in user.education],
            "projects": [p.model_dump() for p in user.projects],
            "preferences": user.preferences.model_dump() if user.preferences else {},
            "career_analysis": user.career_analysis.model_dump() if user.career_analysis else {}
        }

        matched_count = 0

        # Import LLMService lazily from DI container
        from app.application.dependencies.container import get_container
        llm_service = get_container().llm_service

        for job in analyzed_jobs:
            try:
                # Call matching service
                jd_data = job.jd_analysis.model_dump() if job.jd_analysis else {}
                match_results = await llm_service.match_job(profile_data, jd_data)
                
                # Build MatchScore object
                score_val = match_results.get("overall", 0.0)
                score = MatchScore(
                    overall=float(score_val),
                    skill=float(match_results.get("skill", 0.0)),
                    experience=float(match_results.get("experience", 0.0)),
                    education=float(match_results.get("education", 0.0)),
                    location=float(match_results.get("location", 0.0)),
                    salary=float(match_results.get("salary", 0.0)),
                    culture=float(match_results.get("culture", 0.0)),
                )

                # Initialize job application aggregate
                app_entry = ApplicationModel(
                    user_id=user.id,
                    job_id=job.id,
                    match_score=score,
                    status=ApplicationStatus.PENDING_APPROVAL
                )
                app_entry.transition_status(
                    ApplicationStatus.PENDING_APPROVAL,
                    notes=f"Auto-generated application based on match score of {score_val}%. Match summary: {match_results.get('notes', '')}"
                )

                # Save or update application
                existing = await self._application_repo.get_by_user_and_job(user.id, job.id)
                if existing:
                    await self._application_repo.update(existing.id, app_entry.model_dump(exclude={"id"}))
                else:
                    await self._application_repo.create(app_entry)

                # Update job status
                await self._job_repo.update(job.id, {"status": JobStatus.MATCHED})
                
                # Publish event
                event = job_matched_event(
                    source=self.name,
                    job_id=job.id,
                    user_id=user.id,
                    match_score=score.model_dump(),
                )
                await self.publish_event(event)

                matched_count += 1
            except Exception as exc:
                self._logger.error("job_matching_failed", job_id=job.id, error=str(exc))

        return AgentResult(
            success=True,
            data={"matched_count": matched_count},
            message=f"Successfully evaluated and scored {matched_count} job matches."
        )

    async def on_jd_analyzed(self, event: Any) -> None:
        """Triggered automatically via pub/sub when a JD description is analyzed."""
        self._logger.info("job_matcher_event_received", event_type=event.event_type)
        import asyncio
        asyncio.create_task(self.execute())
