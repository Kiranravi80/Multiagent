"""
Memory Manager.

High-level interface for semantic memory operations across different namespaces.
"""

from __future__ import annotations

from typing import Any

from app.core.constants import MemoryType
from app.core.logging import get_logger
from app.infrastructure.memory.vector_store import VectorStore

logger = get_logger(__name__)


class MemoryManager:
    """
    Manages semantic memory across separate namespaces.

    Each MemoryType maps to a separate vector store collection,
    providing isolation between career, learning, news, etc.
    """

    def __init__(self, vector_store: VectorStore) -> None:
        self._store = vector_store

    async def remember(
        self,
        memory_type: MemoryType,
        *,
        content: str,
        metadata: dict[str, Any] | None = None,
        memory_id: str | None = None,
    ) -> None:
        """Store a memory in the appropriate namespace."""
        await self._store.add(
            memory_type.value,
            documents=[content],
            metadatas=[metadata] if metadata else None,
            ids=[memory_id] if memory_id else None,
        )
        logger.debug("memory_stored", type=memory_type.value, length=len(content))

    async def recall(
        self,
        memory_type: MemoryType,
        *,
        query: str,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Retrieve relevant memories from a namespace."""
        results = await self._store.query(
            memory_type.value,
            query_text=query,
            n_results=n_results,
        )
        logger.debug("memory_recalled", type=memory_type.value, results=len(results))
        return results

    async def forget(
        self,
        memory_type: MemoryType,
        *,
        memory_ids: list[str],
    ) -> None:
        """Remove specific memories from a namespace."""
        await self._store.delete(memory_type.value, ids=memory_ids)
