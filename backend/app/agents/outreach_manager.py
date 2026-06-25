"""Outreach Manager Agent.

Manages connection message templates, cold emails drafts, and relationship logs.
All messages are generated as drafts and require explicit human-in-the-loop approval.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.agents.base.agent import AgentResult, BaseAgent
from app.core.constants import EventType
from app.domain.events.base import DomainEvent
from app.domain.models.email import EmailModel
from app.domain.repositories.networking_repository import NetworkingRepository
from app.domain.repositories.user_repository import UserRepository
from app.domain.repositories.email_repository import EmailRepository


class OutreachManager(BaseAgent):
    """AI agent that compiles personalized recruiter messages for review."""

    def __init__(
        self,
        *,
        event_bus: Any,
        networking_repo: NetworkingRepository,
        user_repo: UserRepository,
        email_repo: EmailRepository,
    ) -> None:
        super().__init__(name="outreach_manager", event_bus=event_bus)
        self._networking_repo = networking_repo
        self._user_repo = user_repo
        self._email_repo = email_repo

    async def initialize(self) -> None:
        """Subscribe to contact discovery events."""
        await self.subscribe(EventType.OPPORTUNITY_FOUND, self.on_trigger_event)
        self._logger.info("outreach_manager_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Draft a personalized connection message and save it for review."""
        self._logger.info("outreach_manager_run_started")

        contact_id = context.get("contact_id") if context else None
        if not contact_id:
            # Fallback to latest identified contact
            contacts = await self._networking_repo.find({"status": "identified"})
            if not contacts:
                return AgentResult(success=True, data={"drafted_count": 0}, message="No new contacts available to draft messages for.")
            contact_id = contacts[0].id

        contact = await self._networking_repo.get_by_id(contact_id)
        if not contact:
            return AgentResult(success=False, data={}, message=f"Contact {contact_id} not found.")

        users = await self._user_repo.get_all(limit=1)
        if not users:
            return AgentResult(success=False, data={}, message="No user profile found for outreach manager.")
        user = users[0]

        # Import LLMService lazily
        from app.application.dependencies.container import get_container
        llm_service = get_container().llm_service

        try:
            # Generate outreach note (e.g. LinkedIn invitation text or short email)
            profile_dict = {"skills": user.skills, "bio": user.bio, "experience": user.experience}
            contact_dict = {"name": contact.name, "role": contact.role, "company": contact.company}
            
            draft_data = await llm_service.draft_outreach(profile_data=profile_dict, target_contact=contact_dict)
            message_text = draft_data.get("message", "")
            subject = draft_data.get("subject", "Connecting regarding opportunities")

            # Update contact record
            update_data = {
                "status": "outreach_drafted",
                "interaction_history": contact.interaction_history + [
                    {
                        "date": asyncio.get_event_loop().time(),
                        "type": "draft",
                        "subject": subject,
                        "body": message_text
                    }
                ]
            }
            await self._networking_repo.update(contact.id, update_data)

            # If email is available, queue a draft in the email repository
            email_draft_id = None
            if contact.email:
                email_draft = EmailModel(
                    to_email=contact.email,
                    from_email=user.email,
                    subject=subject,
                    body=message_text,
                    status="draft",
                    type="outbound"
                )
                email_draft_id = await self._email_repo.create(email_draft)

            # Publish event
            event = DomainEvent(
                event_type=EventType.MESSAGE_READY,
                source_agent=self.name,
                payload={
                    "contact_id": contact.id,
                    "email_draft_id": email_draft_id,
                    "message_preview": message_text[:60]
                }
            )
            await self.publish_event(event)

            return AgentResult(
                success=True,
                data={"contact_id": contact.id, "email_draft_id": email_draft_id},
                message=f"Message draft successfully generated for {contact.name}."
            )

        except Exception as exc:
            self._logger.error("outreach_drafting_failed", error=str(exc))
            return AgentResult(success=False, data={}, message=f"Failed to draft outreach: {exc}")

    async def on_trigger_event(self, event: Any) -> None:
        """Asynchronously trigger agent execute on event receipt."""
        self._logger.info("outreach_trigger_received", event_type=event.event_type)
        context = {}
        if event.payload and "contact_id" in event.payload:
            context["contact_id"] = event.payload["contact_id"]
        asyncio.create_task(self.execute(context))
