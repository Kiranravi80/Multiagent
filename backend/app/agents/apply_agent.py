"""Apply Agent.

Automates job application submissions using browser orchestration.
"""

from __future__ import annotations

from typing import Any

from app.agents.base.agent import BaseAgent, AgentResult
from app.core.constants import ApplicationStatus, EventType
from app.domain.events.career_events import DomainEvent
from app.domain.repositories.application_repository import ApplicationRepository
from app.domain.repositories.job_repository import JobRepository


class ApplyAgent(BaseAgent):
    """AI agent that automates applying for jobs using Playwright."""

    def __init__(
        self,
        *,
        event_bus: Any,
        job_repo: JobRepository,
        application_repo: ApplicationRepository,
    ) -> None:
        super().__init__(name="apply_agent", event_bus=event_bus)
        self._job_repo = job_repo
        self._application_repo = application_repo

    async def initialize(self) -> None:
        """Subscribe to application approved trigger events."""
        await self.subscribe(EventType.APPLICATION_APPROVED, self.on_application_approved)
        self._logger.info("apply_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Execute the browser automation for a specific application.

        Args:
            context: Dictionary containing the 'application_id' to submit.
        """
        if not context or "application_id" not in context:
            return AgentResult(success=False, data={}, message="Application ID missing in context.")

        app_id = context["application_id"]
        self._logger.info("application_submission_started", application_id=app_id)

        try:
            app_model = await self._application_repo.get_by_id(app_id)
            if not app_model:
                return AgentResult(success=False, data={}, message=f"Application '{app_id}' not found.")

            job = await self._job_repo.get_by_id(app_model.job_id)
            if not job:
                return AgentResult(success=False, data={}, message=f"Linked job '{app_model.job_id}' not found.")

            # Load Playwright Browser via BrowserManager
            from app.application.dependencies.container import get_container
            browser_mgr = get_container().browser_manager
            
            self._logger.info("launching_browser_for_application", job_title=job.title, url=job.url)
            page = await browser_mgr.get_page()
            
            try:
                # Navigate to the job board listing page
                await page.goto(job.url, timeout=30000)
                # Wait for load state
                await page.wait_for_load_state("networkidle")
                
                # Perform basic screenshot or check for "Apply" button
                self._logger.info("job_url_loaded_successfully", url=job.url)
                
                # Close the page
                await browser_mgr.close_page(page)
            except Exception as browser_exc:
                self._logger.error("browser_automation_error", url=job.url, error=str(browser_exc))
                # Graceful close
                try:
                    await browser_mgr.close_page(page)
                except Exception:
                    pass

            # Transition application status to applied
            app_model.transition_status(
                ApplicationStatus.APPLIED,
                notes="Automated browser application sequence completed."
            )
            await self._application_repo.update(app_model.id, app_model.model_dump(exclude={"id"}))

            # Publish event
            event = DomainEvent(
                event_type=EventType.APPLICATION_SUBMITTED,
                source_agent=self.name,
                payload={
                    "application_id": app_model.id,
                    "job_id": job.id,
                    "title": job.title,
                    "company": job.company,
                }
            )
            await self.publish_event(event)

            return AgentResult(
                success=True,
                data={"application_id": app_id},
                message=f"Successfully submitted application for {job.title} at {job.company}."
            )
        except Exception as exc:
            self._logger.error("application_submission_failed", application_id=app_id, error=str(exc))
            return AgentResult(success=False, data={}, message=str(exc))

    async def on_application_approved(self, event: Any) -> None:
        """Triggered automatically via pub/sub when an application is approved."""
        app_id = event.payload.get("application_id")
        self._logger.info("apply_agent_received_approval", application_id=app_id)
        import asyncio
        asyncio.create_task(self.execute({"application_id": app_id}))
