"""Networking Agent.

Identifies key hiring contacts (recruiters, managers) for matched roles and new startups.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.agents.base.agent import AgentResult, BaseAgent
from app.core.constants import EventType
from app.domain.events.base import DomainEvent
from app.domain.models.networking import NetworkingModel
from app.domain.repositories.networking_repository import NetworkingRepository
from app.domain.repositories.job_repository import JobRepository


class NetworkingAgent(BaseAgent):
    """AI agent that discovers and lists key hiring contacts for relevant roles."""

    def __init__(
        self,
        *,
        event_bus: Any,
        networking_repo: NetworkingRepository,
        job_repo: JobRepository,
    ) -> None:
        super().__init__(name="networking_agent", event_bus=event_bus)
        self._networking_repo = networking_repo
        self._job_repo = job_repo

    async def initialize(self) -> None:
        """Subscribe to job matched and startup detected events."""
        await self.subscribe(EventType.JOB_MATCHED, self.on_trigger_event)
        await self.subscribe(EventType.STARTUP_FOUND, self.on_trigger_event)
        self._logger.info("networking_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Simulate scanning company sites and directories to identify recruiters/leads."""
        self._logger.info("networking_run_started")

        job_id = context.get("job_id") if context else None
        if not job_id:
            # Execute for latest matched job as fallback
            from app.application.dependencies.container import get_container
            app_repo = get_container().application_repo
            apps = await app_repo.get_all(limit=1)
            if not apps:
                return AgentResult(success=True, data={"connections_count": 0}, message="No applications available to scan contacts for.")
            job_id = apps[0].job_id

        job = await self._job_repo.get_by_id(job_id)
        if not job:
            return AgentResult(success=False, data={}, message=f"Job {job_id} not found.")

        # Simulate finding contacts via public APIs/Search
        contacts = [
            {
                "name": f"Hiring Manager at {job.company}",
                "role": "Engineering Manager",
                "company": job.company,
                "linkedin_url": f"https://linkedin.com/in/hiring-manager-{job.company.lower()}",
                "email": f"hiring.manager@{job.company.lower().replace(' ', '')}.com"
            },
            {
                "name": f"Technical Recruiter at {job.company}",
                "role": "Recruiting Coordinator",
                "company": job.company,
                "linkedin_url": f"https://linkedin.com/in/recruiter-{job.company.lower()}",
                "email": f"recruiter@{job.company.lower().replace(' ', '')}.com"
            }
        ]

        added_count = 0
        last_contact_id = None
        for c in contacts:
            # Check if contact already exists
            existing = await self._networking_repo.find({"company": c["company"], "role": c["role"]})
            if existing:
                continue

            contact = NetworkingModel(
                name=c["name"],
                role=c["role"],
                company=c["company"],
                linkedin_url=c["linkedin_url"],
                email=c["email"],
                status="identified"
            )
            contact_id = await self._networking_repo.create(contact)
            last_contact_id = contact_id
            added_count += 1

            # Publish event
            event = DomainEvent(
                event_type=EventType.OPPORTUNITY_FOUND,
                source_agent=self.name,
                payload={
                    "contact_id": contact_id,
                    "company": c["company"],
                    "job_id": job_id
                }
            )
            await self.publish_event(event)

        return AgentResult(
            success=True,
            data={"connections_count": added_count, "last_contact_id": last_contact_id},
            message=f"Discovered and saved {added_count} contact leads for {job.company}."
        )

    async def on_trigger_event(self, event: Any) -> None:
        """Asynchronously trigger agent execute on event receipt."""
        self._logger.info("networking_trigger_received", event_type=event.event_type)
        context = {}
        if event.payload and "job_id" in event.payload:
            context["job_id"] = event.payload["job_id"]
        asyncio.create_task(self.execute(context))
