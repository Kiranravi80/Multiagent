"""
PAIOS Dependency Injection Container.

Centralizes the creation and lifecycle of all services.
FastAPI endpoints depend on this container to get properly
wired service instances.

This replaces all scattered direct imports of `db` and service functions.
"""

from __future__ import annotations

from functools import lru_cache

from app.agents.orchestrator.master_orchestrator import MasterOrchestrator
from app.agents.job_collector_agent import JobCollectorAgent
from app.application.services.agent_orchestration_service import AgentOrchestrationService
from app.application.services.auth_service import AuthService
from app.application.services.job_service import JobService
from app.application.services.profile_service import ProfileService
from app.application.services.resume_service import ResumeService
from app.application.services.user_service import UserService
from app.application.services.metrics_service import MetricsService
from app.application.services.audit_service import AuditService
from app.core.logging import get_logger
from app.core.config import get_settings
from app.infrastructure.ai.llm_service import LLMService
from app.infrastructure.ai.model_manager import ModelManager
from app.infrastructure.browser.browser_manager import BrowserManager
from app.infrastructure.database.mongodb import MongoDBManager
from app.infrastructure.database.repositories.mongo_job_repo import MongoJobRepository
from app.infrastructure.database.repositories.mongo_resume_repo import MongoResumeRepository
from app.infrastructure.database.repositories.mongo_user_repo import MongoUserRepository
from app.infrastructure.database.repositories.mongo_audit_repo import MongoAuditRepository
from app.infrastructure.database.repositories.mongo_agent_state_repo import MongoAgentStateRepository
from app.infrastructure.event_bus.base import EventBus
from app.infrastructure.event_bus.in_memory_bus import InMemoryEventBus
from app.infrastructure.event_bus.redis_bus import RedisEventBus
from app.infrastructure.memory.memory_manager import MemoryManager
from app.infrastructure.memory.vector_store import ChromaVectorStore, InMemoryVectorStore
from app.infrastructure.notifications.notification_manager import NotificationManager
from app.infrastructure.storage.file_storage import FileStorage

logger = get_logger(__name__)


class Container:
    """
    Dependency Injection Container.

    Holds singleton instances of infrastructure and creates
    application services with proper dependencies.

    Lifecycle:
        1. Container() — constructor
        2. await initialize() — connect DB, init AI
        3. Use service properties for dependency injection
        4. await shutdown() — cleanup
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        # Infrastructure singletons
        self._db_manager = MongoDBManager()
        
        if self._settings.use_redis_event_bus:
            self._event_bus: EventBus = RedisEventBus(self._settings.redis_url)
        else:
            self._event_bus = InMemoryEventBus()

        self._model_manager = ModelManager()
        self._file_storage = FileStorage()
        self._vector_store = ChromaVectorStore(self._settings)
        self._memory_manager = MemoryManager(self._vector_store)
        self._browser_manager = BrowserManager(
            headless=self._settings.playwright_headless,
            timeout_ms=self._settings.playwright_timeout_ms,
        )
        self._notification_manager = NotificationManager(self._settings)
        self._metrics_service = MetricsService()
        self._orchestrator: MasterOrchestrator | None = None

        # Repository instances (initialized after DB connect)
        self._user_repo: MongoUserRepository | None = None
        self._job_repo: MongoJobRepository | None = None
        self._resume_repo: MongoResumeRepository | None = None
        self._audit_repo: MongoAuditRepository | None = None
        self._agent_state_repo: MongoAgentStateRepository | None = None
        self._audit_service: AuditService | None = None

    async def initialize(self) -> None:
        """Initialize all infrastructure components."""
        # Event Bus start
        if isinstance(self._event_bus, RedisEventBus):
            await self._event_bus.start()

        # Database
        await self._db_manager.connect()
        await self._db_manager.create_indexes()

        db = self._db_manager.get_database()
        self._user_repo = MongoUserRepository(db.users)
        self._job_repo = MongoJobRepository(db.jobs)
        self._resume_repo = MongoResumeRepository(db.resumes)
        self._audit_repo = MongoAuditRepository(db.audit_logs)
        self._agent_state_repo = MongoAgentStateRepository(db.agent_states)
        
        self._audit_service = AuditService(self._audit_repo)

        # Subscribe AuditService to critical events
        from app.core.constants import EventType
        critical_events = [
            EventType.SYSTEM_STARTED,
            EventType.SYSTEM_SHUTDOWN,
            EventType.AGENT_ERROR,
            EventType.USER_REGISTERED,
            EventType.RESUME_UPLOADED,
            EventType.RESUME_GENERATED,
            EventType.APPLICATION_SUBMITTED,
        ]
        for event_type in critical_events:
            await self._event_bus.subscribe(event_type, self._audit_service.log_event)

        # AI
        await self._model_manager.initialize()

        # Browser
        await self._browser_manager.start()

        # Orchestrator
        self._orchestrator = MasterOrchestrator(event_bus=self._event_bus)
        await self._orchestrator.start()

        # Register agents
        job_collector = JobCollectorAgent(
            event_bus=self._event_bus,
            job_repo=self._job_repo,
        )
        await self._orchestrator.register_agent(job_collector)

        logger.info("container_initialized")

    async def shutdown(self) -> None:
        """Gracefully shut down all infrastructure."""
        if self._orchestrator:
            await self._orchestrator.shutdown()
        await self._browser_manager.stop()
        if isinstance(self._event_bus, RedisEventBus):
            await self._event_bus.stop()
        await self._model_manager.shutdown()
        await self._db_manager.disconnect()
        logger.info("container_shutdown")

    # ── Infrastructure Properties ──────────────────────────────────────────

    @property
    def db_manager(self) -> MongoDBManager:
        return self._db_manager

    @property
    def event_bus(self) -> EventBus:
        return self._event_bus

    @property
    def model_manager(self) -> ModelManager:
        return self._model_manager

    @property
    def orchestrator(self) -> MasterOrchestrator:
        if self._orchestrator is None:
            raise RuntimeError("Container not initialized")
        return self._orchestrator

    @property
    def memory_manager(self) -> MemoryManager:
        return self._memory_manager

    @property
    def browser_manager(self) -> BrowserManager:
        return self._browser_manager

    @property
    def notification_manager(self) -> NotificationManager:
        return self._notification_manager

    # ── Repository Properties ──────────────────────────────────────────────

    @property
    def user_repo(self) -> MongoUserRepository:
        if self._user_repo is None:
            raise RuntimeError("Container not initialized")
        return self._user_repo

    @property
    def job_repo(self) -> MongoJobRepository:
        if self._job_repo is None:
            raise RuntimeError("Container not initialized")
        return self._job_repo

    @property
    def resume_repo(self) -> MongoResumeRepository:
        if self._resume_repo is None:
            raise RuntimeError("Container not initialized")
        return self._resume_repo

    @property
    def audit_repo(self) -> MongoAuditRepository:
        if self._audit_repo is None:
            raise RuntimeError("Container not initialized")
        return self._audit_repo

    @property
    def agent_state_repo(self) -> MongoAgentStateRepository:
        if self._agent_state_repo is None:
            raise RuntimeError("Container not initialized")
        return self._agent_state_repo

    # ── Service Factories ──────────────────────────────────────────────────

    @property
    def auth_service(self) -> AuthService:
        return AuthService(self.user_repo)

    @property
    def user_service(self) -> UserService:
        return UserService(self.user_repo)

    @property
    def profile_service(self) -> ProfileService:
        return ProfileService(self.user_repo)

    @property
    def resume_service(self) -> ResumeService:
        return ResumeService(
            user_repo=self.user_repo,
            llm_service=self.llm_service,
            file_storage=self._file_storage,
        )

    @property
    def job_service(self) -> JobService:
        return JobService(self.job_repo)

    @property
    def llm_service(self) -> LLMService:
        return LLMService(self._model_manager)

    @property
    def agent_orchestration_service(self) -> AgentOrchestrationService:
        return AgentOrchestrationService(self.orchestrator)

    @property
    def metrics_service(self) -> MetricsService:
        return self._metrics_service

    @property
    def audit_service(self) -> AuditService:
        if self._audit_service is None:
            raise RuntimeError("Container not initialized")
        return self._audit_service



# ── Singleton Container ────────────────────────────────────────────────────

_container: Container | None = None


def get_container() -> Container:
    """Get the singleton Container instance."""
    global _container
    if _container is None:
        _container = Container()
    return _container


async def initialize_container() -> Container:
    """Initialize the singleton Container (call once at startup)."""
    container = get_container()
    await container.initialize()
    return container


async def shutdown_container() -> None:
    """Shutdown the singleton Container (call once at shutdown)."""
    global _container
    if _container is not None:
        await _container.shutdown()
        _container = None
