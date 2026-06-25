"""
Vector Store — ChromaDB Integration.

Provides ChromaDB connection and local Ollama-based embeddings.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
import httpx
import chromadb
from chromadb import EmbeddingFunction, Documents, Embeddings

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


class OllamaEmbeddingFunction(EmbeddingFunction):
    """Custom ChromaDB Embedding Function calling local Ollama service."""

    def __init__(self, model_name: str, base_url: str) -> None:
        self.model_name = model_name
        self.base_url = base_url

    def __call__(self, input: Documents) -> Embeddings:
        embeddings: Embeddings = []
        # Query Ollama synchronously within the Chroma execution context
        with httpx.Client(timeout=30.0) as client:
            for doc in input:
                try:
                    response = client.post(
                        f"{self.base_url}/api/embeddings",
                        json={"model": self.model_name, "prompt": doc},
                    )
                    response.raise_for_status()
                    embeddings.append(response.json()["embedding"])
                except Exception as exc:
                    logger.error(
                        "ollama_embedding_generation_failed",
                        model=self.model_name,
                        error=str(exc),
                    )
                    # Return empty dimension array if fail
                    embeddings.append([0.0] * 384)  # Default dim
        return embeddings


class ChromaVectorStore(VectorStore):
    """Concrete vector store using ChromaDB."""

    def __init__(self, settings: Any) -> None:
        self._settings = settings
        if settings.chroma_host:
            self._client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=settings.chroma_port,
            )
        else:
            self._client = chromadb.PersistentClient(path=settings.chroma_persist_dir)

        # Uses the default local Ollama model for embedding generation
        self._embedding_function = OllamaEmbeddingFunction(
            model_name=settings.ollama_default_model,
            base_url=settings.ollama_base_url,
        )
        logger.info("chromadb_vector_store_initialized", host=settings.chroma_host or "local_sqlite")

    async def add(
        self,
        collection: str,
        *,
        documents: list[str],
        metadatas: list[dict[str, Any]] | None = None,
        ids: list[str] | None = None,
    ) -> None:
        col = self._client.get_or_create_collection(
            name=collection,
            embedding_function=self._embedding_function,
        )
        col.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.debug("chroma_add_success", collection=collection, count=len(documents))

    async def query(
        self,
        collection: str,
        *,
        query_text: str,
        n_results: int = 5,
    ) -> list[dict[str, Any]]:
        try:
            col = self._client.get_collection(
                name=collection,
                embedding_function=self._embedding_function,
            )
            results = col.query(
                query_texts=[query_text],
                n_results=n_results,
            )

            formatted = []
            if results and results["documents"]:
                for i in range(len(results["documents"][0])):
                    formatted.append({
                        "document": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "id": results["ids"][0][i],
                    })
            return formatted
        except Exception as exc:
            logger.debug("chroma_query_empty_or_failed", error=str(exc))
            return []

    async def delete(self, collection: str, *, ids: list[str]) -> None:
        try:
            col = self._client.get_collection(
                name=collection,
                embedding_function=self._embedding_function,
            )
            col.delete(ids=ids)
        except Exception as exc:
            logger.error("chroma_delete_failed", collection=collection, error=str(exc))


class InMemoryVectorStore(VectorStore):
    """
    Minimal in-memory vector store for development.

    Does NOT perform actual semantic search — returns results
    by simple substring matching.
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

