"""Content Repository Interface.

Defines the contract for professional content metadata (posts, articles) operations.
"""

from __future__ import annotations

from abc import ABC
from app.domain.models.content import ContentModel
from app.domain.repositories.base import BaseRepository


class ContentRepository(BaseRepository[ContentModel], ABC):
    """Repository interface for professional content drafts and posts."""
    ...
