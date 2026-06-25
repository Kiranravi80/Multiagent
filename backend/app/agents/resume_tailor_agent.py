"""Resume Tailor Agent.

Evaluates ATS fit, generates tailored resumes, and registers custom versions for applications.
"""

from __future__ import annotations

from typing import Any

from app.agents.base.agent import BaseAgent, AgentResult
from app.core.constants import ApplicationStatus, EventType, ResumeType
from app.domain.events.career_events import ats_completed_event, resume_generated_event, application_ready_event
from app.domain.models.resume import ResumeModel
from app.domain.repositories.application_repository import ApplicationRepository
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.resume_repository import ResumeRepository
from app.domain.repositories.user_repository import UserRepository


class ResumeTailorAgent(BaseAgent):
    """AI agent that automates ATS scoring, recruiter evaluation, and resume customization."""

    def __init__(
        self,
        *,
        event_bus: Any,
        job_repo: JobRepository,
        user_repo: UserRepository,
        resume_repo: ResumeRepository,
        application_repo: ApplicationRepository,
    ) -> None:
        super().__init__(name="resume_tailor_agent", event_bus=event_bus)
        self._job_repo = job_repo
        self._user_repo = user_repo
        self._resume_repo = resume_repo
        self._application_repo = application_repo

    async def initialize(self) -> None:
        """Subscribe to job match events."""
        await self.subscribe(EventType.JOB_MATCHED, self.on_job_matched)
        self._logger.info("resume_tailor_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Manual trigger: Customize resumes for matched applications that lack versions."""
        self._logger.info("resume_tailoring_run_started")

        # 1. Fetch PENDING_APPROVAL applications
        pending_apps = await self._application_repo.find({"status": ApplicationStatus.PENDING_APPROVAL})
        if not pending_apps:
            return AgentResult(success=True, data={"tailored_count": 0}, message="No applications pending resume tailoring.")

        tailored_count = 0

        # Import LLMService lazily from DI container
        from app.application.dependencies.container import get_container
        llm_service = get_container().llm_service

        for app_model in pending_apps:
            # Skip if already tailored
            if app_model.resume_version_id and app_model.ats_score:
                continue

            try:
                # 2. Get user original resume text
                user = await self._user_repo.get_by_id(app_model.user_id)
                if not user:
                    continue

                # Query original resume or fallback to user resume text
                resumes = await self._resume_repo.find({"user_id": user.id, "type": ResumeType.ORIGINAL})
                original_text = ""
                if resumes:
                    original_text = resumes[0].raw_text
                else:
                    original_text = user.resume_text

                if not original_text:
                    self._logger.warning("no_resume_found_for_tailoring", user_id=user.id)
                    continue

                # 3. Get job requirements
                job = await self._job_repo.get_by_id(app_model.job_id)
                if not job:
                    continue

                # 4. Tailor Resume via LLM
                tailored_text = await llm_service.tailor_resume(original_text, job.description)

                # 5. Evaluate ATS Score on tailored resume
                ats_eval = await llm_service.evaluate_ats(tailored_text, job.description)
                ats_score = float(ats_eval.get("overall_score", 0.0))

                # 6. Save tailored Resume
                tailored_resume = ResumeModel(
                    user_id=user.id,
                    type=ResumeType.AI_RESUME,
                    file_name=f"resume_tailored_{job.company.lower().strip()}_{job.id[:6]}.md",
                    raw_text=tailored_text,
                    parsed_data=ats_eval,
                    tailored_for_job_id=job.id,
                    ats_score=ats_score
                )
                resume_id = await self._resume_repo.create(tailored_resume)

                # 7. Update Application details
                update_data = {
                    "resume_version_id": resume_id,
                    "ats_score": ats_score,
                }
                app_model.resume_version_id = resume_id
                app_model.ats_score = ats_score
                app_model.transition_status(
                    ApplicationStatus.PENDING_APPROVAL,
                    notes=f"ATS Match complete. Tailored resume saved under ID {resume_id}. Score: {ats_score}%. Target improvements: {', '.join(ats_eval.get('improvements', []))}"
                )
                
                await self._application_repo.update(app_model.id, app_model.model_dump(exclude={"id"}))

                # 8. Publish downstream events
                await self.publish_event(
                    ats_completed_event(
                        source=self.name,
                        resume_id=resume_id,
                        job_id=job.id,
                        ats_score=ats_score,
                        improvements=ats_eval.get("improvements", []),
                    )
                )

                await self.publish_event(
                    resume_generated_event(
                        source=self.name,
                        resume_id=resume_id,
                        resume_type=ResumeType.AI_RESUME.value,
                        user_id=user.id,
                    )
                )

                await self.publish_event(
                    application_ready_event(
                        source=self.name,
                        job_id=job.id,
                        user_id=user.id,
                        resume_id=resume_id,
                        match_score=app_model.match_score.overall,
                    )
                )

                tailored_count += 1
            except Exception as exc:
                self._logger.error("resume_tailoring_failed", app_id=app_model.id, error=str(exc))

        return AgentResult(
            success=True,
            data={"tailored_count": tailored_count},
            message=f"Successfully generated tailored resumes for {tailored_count} applications."
        )

    async def on_job_matched(self, event: Any) -> None:
        """Triggered automatically via pub/sub when a job is matched."""
        self._logger.info("resume_tailor_event_received", event_type=event.event_type)
        import asyncio
        asyncio.create_task(self.execute())
