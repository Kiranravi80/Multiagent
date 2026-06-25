"""GitHub Agent.

Scans user repositories (mocked/simulated) and drafts professional writeups, pinned repo updates, and project documentation.
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


class GitHubAgent(BaseAgent):
    """AI agent that summarizes developer repositories and drafts profiles updates."""

    def __init__(
        self,
        *,
        event_bus: Any,
        content_repo: ContentRepository,
        user_repo: UserRepository,
    ) -> None:
        super().__init__(name="github_agent", event_bus=event_bus)
        self._content_repo = content_repo
        self._user_repo = user_repo

    async def initialize(self) -> None:
        """Subscribe to profile and learning updates."""
        await self.subscribe(EventType.PROFILE_UPDATED, self.on_trigger_event)
        self._logger.info("github_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Analyze user projects and generate GitHub profile README drafts."""
        self._logger.info("github_run_started")

        users = await self._user_repo.get_all(limit=1)
        if not users:
            return AgentResult(success=False, data={}, message="No user profile found for GitHub agent.")
        user = users[0]

        # Fetch projects from user profile
        projects = getattr(user, "projects", [])
        if not projects:
            projects = [{"name": "PAIOS Core", "description": "AI Personal Operating System."}]

        # Import LLMService lazily
        from app.application.dependencies.container import get_container
        llm_service = get_container().llm_service

        try:
            # Generate profile updates or readme summaries
            topic = f"GitHub Profile Overview highlighting {', '.join(user.skills[:5])}"
            content_data = await llm_service.generate_content(
                platform="github",
                topic=topic,
                user_bio=f"Projects: {projects}. Skills: {user.skills}."
            )

            # Create post/content draft
            draft = ContentModel(
                platform="github",
                title=content_data.get("title", "GitHub Profile README Draft"),
                body=content_data.get("body", ""),
                status="draft"
            )
            draft_id = await self._content_repo.create(draft)

            # Publish event
            event = DomainEvent(
                event_type=EventType.CONTENT_GENERATED,
                source_agent=self.name,
                payload={"content_id": draft_id, "platform": "github"}
            )
            await self.publish_event(event)

            return AgentResult(
                success=True,
                data={"content_id": draft_id, "platform": "github"},
                message="GitHub README/writeup draft compiled successfully."
            )

        except Exception as exc:
            self._logger.error("github_readme_draft_failed", error=str(exc))
            return AgentResult(success=False, data={}, message=f"Failed to run GitHub agent: {exc}")

    async def on_trigger_event(self, event: Any) -> None:
        """Asynchronously trigger agent execute on event receipt."""
        self._logger.info("github_trigger_received", event_type=event.event_type)
        asyncio.create_task(self.execute())
