"""Portfolio Agent.

Updates portfolio layout configurations and projects listings dynamically.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.agents.base.agent import AgentResult, BaseAgent
from app.core.constants import EventType
from app.domain.events.base import DomainEvent
from app.domain.models.portfolio import PortfolioModel
from app.domain.repositories.portfolio_repository import PortfolioRepository
from app.domain.repositories.user_repository import UserRepository


class PortfolioAgent(BaseAgent):
    """AI agent that dynamically updates the user's portfolio layout configurations."""

    def __init__(
        self,
        *,
        event_bus: Any,
        portfolio_repo: PortfolioRepository,
        user_repo: UserRepository,
    ) -> None:
        super().__init__(name="portfolio_agent", event_bus=event_bus)
        self._portfolio_repo = portfolio_repo
        self._user_repo = user_repo

    async def initialize(self) -> None:
        """Subscribe to profile and job matcher updates."""
        await self.subscribe(EventType.PROFILE_UPDATED, self.on_trigger_event)
        await self.subscribe(EventType.JOB_MATCHED, self.on_trigger_event)
        self._logger.info("portfolio_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Evaluate profile details and generate updated portfolio metadata."""
        self._logger.info("portfolio_run_started")

        users = await self._user_repo.get_all(limit=1)
        if not users:
            return AgentResult(success=False, data={}, message="No user profile found to update portfolio.")
        user = users[0]

        # Fetch existing portfolio or create placeholder projects
        portfolio = await self._portfolio_repo.get_by_user_id(user.id)
        existing_projects = portfolio.projects if portfolio else []

        # Import LLMService lazily
        from app.application.dependencies.container import get_container
        llm_service = get_container().llm_service

        try:
            profile_dict = {
                "name": user.email.split("@")[0].capitalize(),
                "skills": user.skills,
                "experience": user.experience,
                "education": user.education
            }
            
            # Generate config
            config_data = await llm_service.generate_portfolio_config(
                profile_data=profile_dict,
                projects=existing_projects or [{"title": "PAIOS Digital Twin", "description": "Local AI operating system."}]
            )

            # Save or update portfolio collection
            if portfolio:
                portfolio.bio = config_data.get("bio", portfolio.bio)
                portfolio.skills = config_data.get("skills", portfolio.skills)
                portfolio.projects = config_data.get("projects", portfolio.projects)
                portfolio.layout = config_data.get("layout", portfolio.layout)
                await self._portfolio_repo.update(portfolio.id, portfolio.to_dict())
                portfolio_id = portfolio.id
            else:
                new_portfolio = PortfolioModel(
                    user_id=user.id,
                    bio=config_data.get("bio", ""),
                    skills=config_data.get("skills", []),
                    projects=config_data.get("projects", []),
                    socials={"linkedin": user.linkedin, "github": "", "email": user.email},
                    layout=config_data.get("layout", {})
                )
                portfolio_id = await self._portfolio_repo.create(new_portfolio)

            # Publish event
            event = DomainEvent(
                event_type=EventType.PORTFOLIO_UPDATED,
                source_agent=self.name,
                payload={"portfolio_id": portfolio_id, "user_id": user.id}
            )
            await self.publish_event(event)

            return AgentResult(
                success=True,
                data={"portfolio_id": portfolio_id},
                message="Portfolio layout configuration updated successfully."
            )

        except Exception as exc:
            self._logger.error("portfolio_generation_failed", error=str(exc))
            return AgentResult(success=False, data={}, message=f"Failed to update portfolio: {exc}")

    async def on_trigger_event(self, event: Any) -> None:
        """Asynchronously trigger agent execute on event receipt."""
        self._logger.info("portfolio_trigger_received", event_type=event.event_type)
        asyncio.create_task(self.execute())
