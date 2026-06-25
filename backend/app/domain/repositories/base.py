"""
Base Repository Interface.

Abstract base class defining the contract for all data access.
Infrastructure implementations (MongoDB, PostgreSQL, etc.)
must implement these methods.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class BaseRepository(ABC, Generic[T]):
    """
    Generic repository interface.

    Type parameter T is the domain model class (UserModel, JobModel, etc.).
    All methods are async to support non-blocking I/O.
    """

    @abstractmethod
    async def get_by_id(self, entity_id: str) -> T | None:
        """Retrieve an entity by its ID."""
        ...

    @abstractmethod
    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_order: int = -1,
    ) -> list[T]:
        """
        Retrieve a paginated list of entities.

        Args:
            skip: Number of records to skip.
            limit: Maximum number of records to return.
            sort_by: Field name to sort by.
            sort_order: 1 for ascending, -1 for descending.
        """
        ...

    @abstractmethod
    async def create(self, entity: T) -> str:
        """
        Persist a new entity.

        Returns:
            The ID of the created entity.
        """
        ...

    @abstractmethod
    async def update(self, entity_id: str, data: dict[str, Any]) -> T | None:
        """
        Update an existing entity by ID.

        Args:
            entity_id: The entity to update.
            data: Fields to update (partial update).

        Returns:
            The updated entity, or None if not found.
        """
        ...

    @abstractmethod
    async def delete(self, entity_id: str) -> bool:
        """
        Delete an entity by ID.

        Returns:
            True if the entity was deleted, False if not found.
        """
        ...

    @abstractmethod
    async def count(self, filter_query: dict[str, Any] | None = None) -> int:
        """Count entities matching the optional filter."""
        ...

    @abstractmethod
    async def find(
        self,
        filter_query: dict[str, Any],
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[T]:
        """Find entities matching a filter query."""
        ...
