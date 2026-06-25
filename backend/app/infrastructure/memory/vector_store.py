"""
Vector Store — ChromaDB Integration.

Placeholder for Phase 5. Provides the interface for semantic memory
without requiring ChromaDB installation during Phase 0.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorStore(ABC):
    """Abstract vector store interface for semantic memory."""

    @abstractmethod
    async def add(
        self,
        collection: str,
        *,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        """Add documents to a collection."""
        ...

    @abstractmethod
    async def query(
        self,
        collection: str,
        *,
        query_text: str,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Query similar documents from a collection."""
        ...

    @abstractmethod
    async def delete(self, collection: str, *, ids: list[str]) -> None:
        """Delete documents by ID."""
        ...


class InMemoryVectorStore(VectorStore):
    """
    Minimal in-memory vector store for development.

    Does NOT perform actual semantic search — returns results
    by simple substring matching. Replace with ChromaDB in Phase 5.
    """

    def __init__(self) -> None:
        self._collections: dict[str, list[dict[str, Any]]] = {}

    async def add(
        self,
        collection: str,
        *,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        if collection not in self._collections:
            self._collections[collection] = []

        for i, doc in enumerate(documents):
            entry = {
                "document": doc,
                "metadata": metadatas[i] if metadatas and i < len(metadatas) else {},
                "id": ids[i] if ids and i < len(ids) else str(i),
            }
            self._collections[collection].append(entry)

        logger.debug("vector_store_add", collection=collection, count=len(documents))

    async def query(
        self,
        collection: str,
        *,
        query_text: str,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        items = self._collections.get(collection, [])
        # Simple substring match (replace with actual embeddings in Phase 5)
        query_lower = query_text.lower()
        results = [
            item for item in items if query_lower in item["document"].lower()
        ]
        return results[:n_results]

    async def delete(self, collection: str, *, ids: list[str]) -> None:
        items = self._collections.get(collection, [])
        self._collections[collection] = [
            item for item in items if item["id"] not in ids
        ]
