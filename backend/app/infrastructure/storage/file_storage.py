"""
File Storage Service.

Manages local filesystem operations for uploads, resumes, and generated files.
"""

from __future__ import annotations

from pathlib import Path

import aiofiles

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FileStorage:
    """Async file storage operations."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def save_upload(
        self,
        content: bytes,
        *,
        subdirectory: str = "resumes",
        filename: str,
    ) -> Path:
        """
        Save uploaded file content to disk.

        Args:
            content: Raw file bytes.
            subdirectory: Subdirectory under uploads/.
            filename: Target filename.

        Returns:
            Absolute path to the saved file.
        """
        directory = self._settings.upload_dir / subdirectory
        directory.mkdir(parents=True, exist_ok=True)

        file_path = directory / filename

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)

        logger.info("file_saved", path=str(file_path), size_bytes=len(content))
        return file_path

    async def read_file(self, path: Path | str) -> bytes:
        """Read file content from disk."""
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    async def delete_file(self, path: Path | str) -> bool:
        """Delete a file from disk."""
        p = Path(path)
        if p.exists():
            p.unlink()
            logger.info("file_deleted", path=str(p))
            return True
        return False

    async def file_exists(self, path: Path | str) -> bool:
        """Check if a file exists."""
        return Path(path).exists()

    def ensure_directory(self, path: Path | str) -> None:
        """Create a directory and all parents if they don't exist."""
        Path(path).mkdir(parents=True, exist_ok=True)
