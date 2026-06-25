import pytest
from unittest.mock import MagicMock, patch

from app.infrastructure.memory.vector_store import ChromaVectorStore, InMemoryVectorStore


@pytest.mark.asyncio
async def test_in_memory_vector_store() -> None:
    """Test standard in-memory vector store operations."""
    store = InMemoryVectorStore()
    await store.add(
        "test_collection",
        documents=["This is a test doc about coding."],
        metadatas=[{"type": "job"}],
        ids=["id_1"],
    )

    results = await store.query("test_collection", query_text="coding")
    assert len(results) == 1
    assert results[0]["id"] == "id_1"


@pytest.mark.asyncio
async def test_chroma_vector_store_mocked() -> None:
    """Test ChromaDB client initialization."""
    with patch("app.infrastructure.memory.vector_store.chromadb.PersistentClient") as mock_persistent:
        mock_client = MagicMock()
        mock_persistent.return_value = mock_client

        settings = MagicMock()
        settings.chroma_host = ""
        settings.chroma_persist_dir = "test_dir"
        settings.ollama_default_model = "llama"
        settings.ollama_base_url = "http://localhost:11434"

        store = ChromaVectorStore(settings)
        assert store._client is not None
