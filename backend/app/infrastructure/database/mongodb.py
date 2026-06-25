"""
MongoDB Connection Manager.

Manages the Motor async client lifecycle:
- Lazy connection on first access
- Connection pooling
- Health checks
- Graceful disconnection

Replaces the old database.py that created a global client at import time.
"""

from __future__ import annotations

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase

from app.core.config import get_settings
from app.core.exceptions import DatabaseError
from app.core.logging import get_logger

logger = get_logger(__name__)


class MongoDBManager:
    """
    Async MongoDB connection manager.

    Usage:
        manager = MongoDBManager()
        await manager.connect()
        db = manager.get_database()
        ...
        await manager.disconnect()
    """

    def __init__(self) -> None:
        self._client: AsyncIOMotorClient | None = None
        self._database: AsyncIOMotorDatabase | None = None

    async def connect(self) -> None:
        """
        Establish connection to MongoDB Atlas.

        Raises:
            DatabaseError: If connection fails.
        """
        settings = get_settings()

        try:
            self._client = AsyncIOMotorClient(
                settings.mongodb_uri,
                maxPoolSize=20,
                minPoolSize=5,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=5000,
            )
            self._database = self._client[settings.database_name]

            # Verify connection with a ping
            await self._client.admin.command("ping")
            logger.info(
                "mongodb_connected",
                database=settings.database_name,
            )

        except Exception as exc:
            logger.error("mongodb_connection_failed", error=str(exc))
            raise DatabaseError(
                f"Failed to connect to MongoDB: {exc}",
                details={"database": settings.database_name},
            )

    async def disconnect(self) -> None:
        """Close the MongoDB connection gracefully."""
        if self._client is not None:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("mongodb_disconnected")

    async def health_check(self) -> bool:
        """
        Ping the database to verify connectivity.

        Returns:
            True if the database is reachable.
        """
        if self._client is None:
            return False
        try:
            await self._client.admin.command("ping")
            return True
        except Exception:
            return False

    def get_database(self) -> AsyncIOMotorDatabase:
        """
        Return the database instance.

        Raises:
            DatabaseError: If not connected.
        """
        if self._database is None:
            raise DatabaseError("MongoDB not connected. Call connect() first.")
        return self._database

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """
        Return a collection by name.

        Raises:
            DatabaseError: If not connected.
        """
        return self.get_database()[name]

    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._database is not None

    async def create_indexes(self) -> None:
        """
        Create all required indexes.

        Called once at startup to ensure optimal query performance.
        """
        db = self.get_database()

        # Users collection
        await db.users.create_index("email", unique=True)

        # Jobs collection
        await db.jobs.create_index("fingerprint", unique=True)
        await db.jobs.create_index("source")
        await db.jobs.create_index("status")
        await db.jobs.create_index("collected_at")

        # Applications collection
        await db.applications.create_index("user_id")
        await db.applications.create_index("job_id")
        await db.applications.create_index([("user_id", 1), ("job_id", 1)], unique=True)

        # Resumes collection
        await db.resumes.create_index("user_id")
        await db.resumes.create_index([("user_id", 1), ("type", 1)])

        # Events collection (audit trail)
        await db.events.create_index("event_type")
        await db.events.create_index("timestamp")
        await db.events.create_index("correlation_id")

        # Agent states collection
        await db.agent_states.create_index("agent_name", unique=True)

        # Digests collection
        await db.digests.create_index("type")
        await db.digests.create_index("created_at")

        # Learning plans collection
        await db.learning_plans.create_index("user_id")

        # Knowledge collection
        await db.knowledge.create_index("type")
        await db.knowledge.create_index("created_at")

        logger.info("mongodb_indexes_created")
