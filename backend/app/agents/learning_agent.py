"""Learning Agent.

Analyzes user skill gaps against matching job requirements and schedules structured learning roadmaps.
"""

from __future__ import annotations

from typing import Any

from app.agents.base.agent import BaseAgent, AgentResult
from app.core.constants import EventType
from app.domain.models.learning_plan import LearningPlanModel, LearningTask
from app.domain.repositories.learning_plan_repository import LearningPlanRepository
from app.domain.repositories.user_repository import UserRepository


class LearningAgent(BaseAgent):
    """AI agent that maps skill gaps to customized study plans."""

    def __init__(
        self,
        *,
        event_bus: Any,
        user_repo: UserRepository,
        learning_plan_repo: LearningPlanRepository,
    ) -> None:
        super().__init__(name="learning_agent", event_bus=event_bus)
        self._user_repo = user_repo
        self._learning_plan_repo = learning_plan_repo

    async def initialize(self) -> None:
        """Subscribe to profile analysis completion trigger events."""
        await self.subscribe(EventType.PROFILE_ANALYZED, self.on_profile_analyzed)
        self._logger.info("learning_agent_initialized")

    async def execute(self, context: dict[str, Any] | None = None) -> AgentResult:
        """Analyze user gaps and compile a structured learning path."""
        self._logger.info("learning_plan_generation_started")

        # 1. Fetch PAIOS User
        users = await self._user_repo.get_all(limit=1)
        if not users:
            return AgentResult(success=False, data={}, message="No user registered in PAIOS. Skill analysis skipped.")
        user = users[0]

        # 2. Extract skill gap
        missing_skills = []
        if user.career_analysis and user.career_analysis.missing_skills:
            missing_skills = user.career_analysis.missing_skills
        else:
            # Fallback placeholder skills to learn
            missing_skills = ["FastAPI", "Docker", "Kubernetes", "Redis", "Celery"]

        if not missing_skills:
            return AgentResult(success=True, data={}, message="User has no identified skill gaps. No plan needed.")

        # 3. Generate learning plan via LLM
        try:
            # Import LLMService lazily from DI container
            from app.application.dependencies.container import get_container
            llm_service = get_container().llm_service
            
            plan_data = await llm_service.generate_learning_plan(user.skills, missing_skills)
            
            tasks = []
            for t in plan_data.get("tasks", []):
                tasks.append(
                    LearningTask(
                        topic=t.get("topic", ""),
                        description=t.get("description", ""),
                        estimated_hours=float(t.get("estimated_hours", 1.0)),
                        status="pending"
                    )
                )

            learning_plan = LearningPlanModel(
                user_id=user.id,
                title=plan_data.get("title", f"PAIOS Learning Plan for {', '.join(missing_skills[:3])}"),
                target_skills=missing_skills,
                tasks=tasks,
                status="in_progress"
            )

            plan_id = await self._learning_plan_repo.create(learning_plan)
            self._logger.info("learning_plan_saved", plan_id=plan_id)

            # Publish event
            from app.domain.events.base import DomainEvent
            await self.publish_event(
                DomainEvent(
                    event_type=EventType.LEARNING_PLAN_CREATED,
                    source_agent=self.name,
                    payload={"plan_id": plan_id, "title": learning_plan.title, "user_id": user.id}
                )
            )

            return AgentResult(
                success=True,
                data={"plan_id": plan_id},
                message=f"Successfully compiled learning plan: {learning_plan.title}"
            )
        except Exception as exc:
            self._logger.error("learning_plan_generation_failed", error=str(exc))
            return AgentResult(success=False, data={}, message=str(exc))

    async def on_profile_analyzed(self, event: Any) -> None:
        """Triggered automatically via pub/sub when user profile analysis is completed."""
        self._logger.info("learning_agent_event_received", event_type=event.event_type)
        import asyncio
        asyncio.create_task(self.execute())
