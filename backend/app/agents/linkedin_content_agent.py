"""LinkedIn Content Agent.

Generates professional technical content drafts for LinkedIn.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.agents.base.agent import AgentResult, BaseAgent
from app.core.constants import EventType
from app.domain.events.base import DomainEvent
from app.domain.models.content import ContentModel
from app.domain.repositories.content_repository import ContentRepository
from app.domain.repositories.user_repository import UserRepository


class LinkedInContentAgent(BaseAgent):
    """AI agent that drafts tech articles and project highlights for LinkedIn."""

    def __init__(
        self,
        *,
        event_bus: Any,
        content_repo: ContentRepository,
        user_repo: UserRepository,
    ) -> None:
        super().__init__(name="linkedin_content_agent", event_bus=event_bus)
        self._content_repo = content_repo
        self._user_repo = user_repo

    async def initialize(self) -> None:
        """Subscribe to learning and digest events."""
        await self.subscribe(EventType.SKILL_GAP_IDENTIFIED, self.on_trigger_event)
        await self.subscribe(EventType.DIGEST_GENERATED, self.on_trigger_event)
        self._logger.info("linkedin_content_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Generate a LinkedIn post draft."""
        self._logger.info("linkedin_content_run_started")

        users = await self._user_repo.get_all(limit=1)
        if not users:
            return AgentResult(success=False, data={}, message="No user profile found to draft content.")
        user = users[0]

        # Use topic from context or fallback to default
        topic = "Modern AI architectures and agent-driven workflows"
        if context and "topic" in context:
            topic = context["topic"]
        elif context and "skills" in context:
            skills = context["skills"]
            topic = f"Insights on learning {', '.join(skills[:3])} for modern systems"

        # Import LLMService lazily
        from app.application.dependencies.container import get_container
        llm_service = get_container().llm_service

        try:
            content_data = await llm_service.generate_content(
                platform="linkedin",
                topic=topic,
                user_bio=user.bio or f"Software Engineer skilled in {', '.join(user.skills)}"
            )

            # Save post as draft (HIL approval required)
            post = ContentModel(
                platform="linkedin",
                title=content_data.get("title", f"Thoughts on {topic}"),
                body=content_data.get("body", ""),
                status="draft"
            )
            post_id = await self._content_repo.create(post)

            # Publish event
            event = DomainEvent(
                event_type=EventType.CONTENT_GENERATED,
                source_agent=self.name,
                payload={"content_id": post_id, "platform": "linkedin"}
            )
            await self.publish_event(event)

            return AgentResult(
                success=True,
                data={"content_id": post_id, "platform": "linkedin"},
                message="LinkedIn post draft generated successfully and saved for approval."
            )

        except Exception as exc:
            self._logger.error("linkedin_content_generation_failed", error=str(exc))
            return AgentResult(success=False, data={}, message=f"Failed to generate LinkedIn content: {exc}")

    async def on_trigger_event(self, event: Any) -> None:
        """Asynchronously trigger agent execute on event receipt."""
        self._logger.info("linkedin_content_trigger_received", event_type=event.event_type)
        context = {}
        if event.payload:
            if "skills" in event.payload:
                context["skills"] = event.payload["skills"]
            if "topic" in event.payload:
                context["topic"] = event.payload["topic"]
        asyncio.create_task(self.execute(context))
