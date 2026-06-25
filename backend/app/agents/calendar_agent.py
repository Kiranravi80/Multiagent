"""Calendar Agent.

Detects proposed interview slots from recruiter emails and schedules calendar holds.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, UTC
from typing import Any

from app.agents.base.agent import AgentResult, BaseAgent
from app.core.constants import EventType
from app.domain.events.base import DomainEvent
from app.domain.models.calendar import CalendarEventModel
from app.domain.repositories.calendar_repository import CalendarRepository
from app.domain.repositories.email_repository import EmailRepository


class CalendarAgent(BaseAgent):
    """AI agent that manages scheduled recruiter holds and interview slots."""

    def __init__(
        self,
        *,
        event_bus: Any,
        calendar_repo: CalendarRepository,
        email_repo: EmailRepository,
    ) -> None:
        super().__init__(name="calendar_agent", event_bus=event_bus)
        self._calendar_repo = calendar_repo
        self._email_repo = email_repo

    async def initialize(self) -> None:
        """Subscribe to incoming email events."""
        await self.subscribe(EventType.EMAIL_READY, self.on_trigger_event)
        self._logger.info("calendar_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Scan received emails and update calendar schedules."""
        self._logger.info("calendar_agent_run_started")

        email_id = context.get("email_id") if context else None
        if not email_id:
            # Fallback to latest received email
            emails = await self._email_repo.find({"type": "inbound", "status": "received"})
            if not emails:
                return AgentResult(success=True, data={"holds_created": 0}, message="No inbound recruiter emails to check for scheduling.")
            email_id = emails[0].id

        email = await self._email_repo.get_by_id(email_id)
        if not email:
            return AgentResult(success=False, data={}, message=f"Email {email_id} not found.")

        # Analyze email body for scheduling intent
        body_lower = email.body.lower()
        if "schedule" not in body_lower and "calendar" not in body_lower and "interview" not in body_lower:
            return AgentResult(success=True, data={"holds_created": 0}, message="No scheduling intent detected in email.")

        # Simulate slot extraction
        start_time = datetime.now(UTC) + timedelta(days=3, hours=10)  # Mock 3 days from now at 10 AM UTC
        end_time = start_time + timedelta(minutes=30)

        # Create calendar hold
        event = CalendarEventModel(
            title=f"Mock Interview / recruiter call with {email.from_email.split('@')[0]}",
            description=f"Automated hold created from email thread {email.thread_id}.",
            start_time=start_time,
            end_time=end_time,
            attendees=[email.to_email, email.from_email],
            status="scheduled"
        )
        event_id = await self._calendar_repo.create(event)

        # Publish CALENDAR_EVENT_CREATED event
        pub_event = DomainEvent(
            event_type=EventType.CALENDAR_EVENT_CREATED,
            source_agent=self.name,
            payload={
                "event_id": event_id,
                "title": event.title,
                "start_time": start_time.isoformat()
            }
        )
        await self.publish_event(pub_event)

        return AgentResult(
            success=True,
            data={"holds_created": 1, "event_id": event_id},
            message=f"Created interview hold '{event.title}' in the calendar."
        )

    async def on_trigger_event(self, event: Any) -> None:
        """Asynchronously trigger agent execute on event receipt."""
        self._logger.info("calendar_trigger_received", event_type=event.event_type)
        context = {}
        if event.payload and "email_id" in event.payload:
            context["email_id"] = event.payload["email_id"]
        asyncio.create_task(self.execute(context))
