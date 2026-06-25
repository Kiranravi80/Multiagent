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
from app.application.services.auth_service import AuthService
from app.application.services.job_service import JobService
from app.application.services.profile_service import ProfileService
from app.application.services.resume_service import ResumeService
from app.application.services.user_service import UserService
from app.core.logging import get_logger
from app.infrastructure.ai.llm_service import LLMService
from app.infrastructure.ai.model_manager import ModelManager
from app.infrastructure.database.mongodb import MongoDBManager
from app.infrastructure.database.repositories.mongo_job_repo import MongoJobRepository
from app.infrastructure.database.repositories.mongo_resume_repo import MongoResumeRepository
from app.infrastructure.database.repositories.mongo_user_repo import MongoUserRepository
from app.infrastructure.event_bus.base import EventBus
from app.infrastructure.event_bus.in_memory_bus import InMemoryEventBus
from app.infrastructure.memory.memory_manager import MemoryManager
from app.infrastructure.memory.vector_store import InMemoryVectorStore
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
        # Infrastructure singletons
        self._db_manager = MongoDBManager()
        self._event_bus: EventBus = InMemoryEventBus()
        self._model_manager = ModelManager()
        self._file_storage = FileStorage()
        self._vector_store = InMemoryVectorStore()
        self._memory_manager = MemoryManager(self._vector_store)
        self._orchestrator: MasterOrchestrator | None = None

        # Repository instances (initialized after DB connect)
        self._user_repo: MongoUserRepository | None = None
        self._job_repo: MongoJobRepository | None = None
        self._resume_repo: MongoResumeRepository | None = None

    async def initialize(self) -> None:
        """Initialize all infrastructure components."""
        # Database
        await self._db_manager.connect()
        await self._db_manager.create_indexes()

        db = self._db_manager.get_database()
        self._user_repo = MongoUserRepository(db.users)
        self._job_repo = MongoJobRepository(db.jobs)
        self._resume_repo = MongoResumeRepository(db.resumes)

        # AI
        await self._model_manager.initialize()

        # Orchestrator
        self._orchestrator = MasterOrchestrator(event_bus=self._event_bus)
        await self._orchestrator.start()

        logger.info("container_initialized")

    async def shutdown(self) -> None:
        """Gracefully shut down all infrastructure."""
        if self._orchestrator:
            await self._orchestrator.shutdown()
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
