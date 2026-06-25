"""Digest Agent.

Aggregates collected tech news, research papers, and startup funding updates into periodic digests.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from app.agents.base.agent import BaseAgent, AgentResult
from app.core.constants import EventType
from app.domain.models.digest import DigestModel
from app.domain.repositories.digest_repository import DigestRepository
from app.domain.repositories.knowledge_repository import KnowledgeRepository


class DigestAgent(BaseAgent):
    """AI agent that compiles daily, weekly, and monthly system summaries."""

    def __init__(
        self,
        *,
        event_bus: Any,
        knowledge_repo: KnowledgeRepository,
        digest_repo: DigestRepository,
    ) -> None:
        super().__init__(name="digest_agent", event_bus=event_bus)
        self._knowledge_repo = knowledge_repo
        self._digest_repo = digest_repo

    async def initialize(self) -> None:
        """Initialize configurations."""
        self._logger.info("digest_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Aggregate news, research, and startups into a single daily summary."""
        self._logger.info("digest_compilation_started")

        digest_type = (context or {}).get("type", "daily")

        # 1. Fetch recent knowledge elements
        try:
            news = await self._knowledge_repo.find({"type": "news"}, limit=5)
            startups = await self._knowledge_repo.find({"type": "startup"}, limit=5)
            papers = await self._knowledge_repo.find({"type": "paper"}, limit=5)
            repos = await self._knowledge_repo.find({"type": "repository"}, limit=5)
            
            # 2. Call LLM to summarize
            summary_prompt = (
                f"Create a concise daily overview summarizing the following tech details:\n\n"
                f"News: {', '.join(n.title for n in news)}\n"
                f"Startups: {', '.join(s.title for s in startups)}\n"
                f"Research: {', '.join(p.title for p in papers)}\n"
                f"Open Source: {', '.join(r.title for r in repos)}"
            )

            # Import LLMService lazily from DI container
            from app.application.dependencies.container import get_container
            llm_service = get_container().llm_service
            
            summary_text = await llm_service.generate_text(summary_prompt, system="You are a senior tech editor. Compile a summary.")

            digest = DigestModel(
                title=f"PAIOS Technical Digest — {datetime.now(UTC).strftime('%B %d, %Y')}",
                type=digest_type,
                summary=summary_text,
                news_highlights=[n.model_dump() for n in news],
                startup_discoveries=[s.model_dump() for s in startups],
                github_trends=[r.model_dump() for r in repos],
                research_papers=[p.model_dump() for p in papers]
            )

            digest_id = await self._digest_repo.create(digest)
            self._logger.info("digest_saved", digest_id=digest_id)

            # Publish event
            from app.domain.events.base import DomainEvent
            await self.publish_event(
                DomainEvent(
                    event_type=EventType.DIGEST_GENERATED,
                    source_agent=self.name,
                    payload={"digest_id": digest_id, "title": digest.title}
                )
            )

            return AgentResult(
                success=True,
                data={"digest_id": digest_id},
                message=f"Successfully compiled digest: {digest.title}"
            )
        except Exception as exc:
            self._logger.error("digest_compilation_failed", error=str(exc))
            return AgentResult(success=False, data={}, message=str(exc))
