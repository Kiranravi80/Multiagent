"""Job Alert Agent.

Monitors pipeline matching outcomes and pushes user notices for top candidates.
"""

from __future__ import annotations

from typing import Any

from app.agents.base.agent import BaseAgent, AgentResult
from app.core.constants import EventType
from app.domain.repositories.job_repository import JobRepository
from app.domain.repositories.user_repository import UserRepository


class JobAlertAgent(BaseAgent):
    """AI agent that notifies the user of highly relevant, ready job openings."""

    def __init__(
        self,
        *,
        event_bus: Any,
        job_repo: JobRepository,
        user_repo: UserRepository,
    ) -> None:
        super().__init__(name="job_alert_agent", event_bus=event_bus)
        self._job_repo = job_repo
        self._user_repo = user_repo

    async def initialize(self) -> None:
        """Subscribe to application ready events."""
        await self.subscribe(EventType.APPLICATION_READY, self.on_application_ready)
        self._logger.info("job_alert_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Manual execution context (optional)."""
        return AgentResult(success=True, data={}, message="Alert agent running.")

    async def on_application_ready(self, event: Any) -> None:
        """Triggered automatically via pub/sub when a job application is ready."""
        payload = event.payload
        job_id = payload.get("job_id")
        match_score = payload.get("match_score", 0.0)

        # Notify only for highly matching jobs (e.g. >= 75%)
        if match_score < 75.0:
            return

        self._logger.info("job_alert_triggered", job_id=job_id, match_score=match_score)

        try:
            job = await self._job_repo.get_by_id(job_id)
            if not job:
                return

            # Construct details message
            message = (
                f"🚨 *PAIOS Match Alert: High-Quality Opportunity Found!*\n\n"
                f"💼 *Title:* {job.title}\n"
                f"🏢 *Company:* {job.company}\n"
                f"📍 *Location:* {job.location}\n"
                f"🎯 *Match Score:* {match_score}%\n"
                f"🌍 *Source:* {job.source.value}\n"
                f"🔗 *Apply Link:* {job.url}\n\n"
                f"Go to the Admin Dashboard to review your tailored resume and submit the application."
            )

            # Retrieve notification manager from container
            from app.application.dependencies.container import get_container
            notification_mgr = get_container().notification_manager
            
            await notification_mgr.notify(
                message=message,
                subject=f"PAIOS Match Alert - {job.title} at {job.company}"
            )
            self._logger.info("job_alert_dispatched", job_id=job_id)
            
        except Exception as exc:
            self._logger.error("job_alert_dispatch_failed", job_id=job_id, error=str(exc))
