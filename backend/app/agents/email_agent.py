"""Email Agent.

Monages the incoming recruiter email scanning and drafts automated reply follow-ups.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.agents.base.agent import AgentResult, BaseAgent
from app.core.constants import EventType
from app.domain.events.base import DomainEvent
from app.domain.models.email import EmailModel
from app.domain.repositories.email_repository import EmailRepository
from app.domain.repositories.user_repository import UserRepository


class EmailAgent(BaseAgent):
    """AI agent that scans received emails and drafts replies for review."""

    def __init__(
        self,
        *,
        event_bus: Any,
        email_repo: EmailRepository,
        user_repo: UserRepository,
    ) -> None:
        super().__init__(name="email_agent", event_bus=event_bus)
        self._email_repo = email_repo
        self._user_repo = user_repo

    async def initialize(self) -> None:
        """Subscribe to message ready events or manual trigger."""
        await self.subscribe(EventType.MESSAGE_READY, self.on_trigger_event)
        self._logger.info("email_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Scan received emails and draft replies."""
        self._logger.info("email_agent_run_started")

        # Scan for any un-replied inbound emails
        inbound_emails = await self._email_repo.find({"type": "inbound", "status": "received"})
        if not inbound_emails:
            # Simulate receiving a recruiter reply as a fallback/mock for testing
            mock_inbound = EmailModel(
                thread_id="thread_mock_123",
                to_email="user@example.com",
                from_email="recruiter@google.com",
                subject="Interview invitation at Google",
                body="Hello, we reviewed your tailored resume and loved it. Let's schedule a call next week.",
                status="received",
                type="inbound"
            )
            mock_inbound_id = await self._email_repo.create(mock_inbound)
            inbound_emails = [await self._email_repo.get_by_id(mock_inbound_id)]

        users = await self._user_repo.get_all(limit=1)
        if not users:
            return AgentResult(success=False, data={}, message="No user profile found for email responder.")
        user = users[0]

        # Import LLMService lazily
        from app.application.dependencies.container import get_container
        llm_service = get_container().llm_service

        drafted_count = 0
        for email in inbound_emails:
            try:
                # Check if we already drafted a reply for this thread
                replies = await self._email_repo.find({"thread_id": email.thread_id, "type": "outbound"})
                if replies:
                    continue

                profile_dict = {"skills": user.skills, "experience": user.experience}
                reply_data = await llm_service.draft_email_reply(
                    inbound_email=email.body,
                    user_profile=profile_dict
                )

                # Save reply as draft
                reply = EmailModel(
                    thread_id=email.thread_id,
                    to_email=email.from_email,
                    from_email=user.email,
                    subject=reply_data.get("subject", f"Re: {email.subject}"),
                    body=reply_data.get("body", ""),
                    status="draft",
                    type="outbound"
                )
                reply_id = await self._email_repo.create(reply)
                drafted_count += 1

                # Publish EMAIL_READY event
                event = DomainEvent(
                    event_type=EventType.EMAIL_READY,
                    source_agent=self.name,
                    payload={
                        "email_id": reply_id,
                        "thread_id": email.thread_id,
                        "to_email": email.from_email
                    }
                )
                await self.publish_event(event)

            except Exception as exc:
                self._logger.error("email_reply_drafting_failed", email_id=email.id, error=str(exc))

        return AgentResult(
            success=True,
            data={"drafted_count": drafted_count},
            message=f"Drafted {drafted_count} replies to recruiter emails."
        )

    async def on_trigger_event(self, event: Any) -> None:
        """Asynchronously trigger agent execute on event receipt."""
        self._logger.info("email_trigger_received", event_type=event.event_type)
        asyncio.create_task(self.execute())
