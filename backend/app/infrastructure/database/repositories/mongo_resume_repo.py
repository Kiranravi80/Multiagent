"""
MongoDB Resume Repository.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.constants import ResumeType
from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.domain.models.resume import ResumeModel
from app.domain.repositories.resume_repository import ResumeRepository

logger = get_logger(__name__)


def _doc_to_model(doc: dict[str, Any]) -> ResumeModel:
    doc["id"] = str(doc.pop("_id"))
    return ResumeModel.model_validate(doc)


class MongoResumeRepository(ResumeRepository):
    """MongoDB implementation of the Resume repository."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    async def get_by_id(self, entity_id: str) -> ResumeModel | None:
        doc = await self._collection.find_one({"_id": ObjectId(entity_id)})
        return _doc_to_model(doc) if doc else None

    async def get_all(
        self, *, skip: int = 0, limit: int = 100, sort_by: str | None = "created_at", sort_order: int = -1
    ) -> list[ResumeModel]:
        cursor = self._collection.find().skip(skip).limit(limit)
        if sort_by:
            cursor = cursor.sort(sort_by, sort_order)
        return [_doc_to_model(doc) async for doc in cursor]

    async def create(self, entity: ResumeModel) -> str:
        doc = entity.model_dump(exclude={"id"})
        doc["created_at"] = datetime.now(UTC)
        try:
            result = await self._collection.insert_one(doc)
            return str(result.inserted_id)
        except Exception as exc:
            raise DatabaseError(f"Failed to create resume: {exc}")

    async def update(self, entity_id: str, data: dict[str, Any]) -> ResumeModel | None:
        await self._collection.update_one({"_id": ObjectId(entity_id)}, {"$set": data})
        return await self.get_by_id(entity_id)

    async def delete(self, entity_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(entity_id)})
        return result.deleted_count > 0

    async def count(self, filter_query: dict[str, Any] | None = None) -> int:
        return await self._collection.count_documents(filter_query or {})

    async def find(self, filter_query: dict[str, Any], *, skip: int = 0, limit: int = 100) -> list[ResumeModel]:
        cursor = self._collection.find(filter_query).skip(skip).limit(limit)
        return [_doc_to_model(doc) async for doc in cursor]

    # ── Resume-specific methods ────────────────────────────────────────────

    async def find_by_user(
        self, user_id: str, *, resume_type: ResumeType | None = None
    ) -> list[ResumeModel]:
        query: dict[str, Any] = {"user_id": user_id}
        if resume_type:
            query["type"] = resume_type.value
        return await self.find(query)

    async def find_latest_by_user(
        self, user_id: str, *, resume_type: ResumeType | None = None
    ) -> ResumeModel | None:
        query: dict[str, Any] = {"user_id": user_id}
        if resume_type:
            query["type"] = resume_type.value
        doc = await self._collection.find_one(query, sort=[("created_at", -1)])
        return _doc_to_model(doc) if doc else None

    async def find_by_job(self, job_id: str, user_id: str) -> ResumeModel | None:
        doc = await self._collection.find_one(
            {"tailored_for_job_id": job_id, "user_id": user_id}
        )
        return _doc_to_model(doc) if doc else None
