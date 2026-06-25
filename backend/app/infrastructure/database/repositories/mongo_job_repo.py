"""
MongoDB Job Repository.

Concrete implementation of JobRepository for MongoDB via Motor.
Supports bulk insert with fingerprint-based dedup.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection
from pymongo.errors import BulkWriteError

from app.core.constants import JobSource, JobStatus
from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.domain.models.job import JobModel
from app.domain.repositories.job_repository import JobRepository

logger = get_logger(__name__)


def _doc_to_model(doc: dict[str, Any]) -> JobModel:
    """Convert a MongoDB document to a JobModel."""
    doc["id"] = str(doc.pop("_id"))
    return JobModel.model_validate(doc)


def _model_to_doc(model: JobModel) -> dict[str, Any]:
    """Convert a JobModel to a MongoDB insert-ready document."""
    data = model.model_dump(exclude={"id"})
    data["fingerprint"] = model.fingerprint
    return data


class MongoJobRepository(JobRepository):
    """MongoDB implementation of the Job repository."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    async def get_by_id(self, entity_id: str) -> JobModel | None:
        try:
            doc = await self._collection.find_one({"_id": ObjectId(entity_id)})
        except Exception as exc:
            raise DatabaseError(f"Failed to get job: {exc}")
        if doc is None:
            return None
        return _doc_to_model(doc)

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = "collected_at",
        sort_order: int = -1,
    ) -> list[JobModel]:
        cursor = self._collection.find().skip(skip).limit(limit)
        if sort_by:
            cursor = cursor.sort(sort_by, sort_order)

        jobs: list[JobModel] = []
        async for doc in cursor:
            jobs.append(_doc_to_model(doc))
        return jobs

    async def create(self, entity: JobModel) -> str:
        doc = _model_to_doc(entity)
        doc["collected_at"] = datetime.now(UTC)

        try:
            result = await self._collection.insert_one(doc)
            return str(result.inserted_id)
        except Exception as exc:
            if "duplicate key" in str(exc).lower():
                logger.debug("job_duplicate_skipped", fingerprint=entity.fingerprint)
                return ""
            raise DatabaseError(f"Failed to create job: {exc}")

    async def update(self, entity_id: str, data: dict[str, Any]) -> JobModel | None:
        try:
            await self._collection.update_one(
                {"_id": ObjectId(entity_id)},
                {"$set": data},
            )
        except Exception as exc:
            raise DatabaseError(f"Failed to update job: {exc}")
        return await self.get_by_id(entity_id)

    async def delete(self, entity_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(entity_id)})
        return result.deleted_count > 0

    async def count(self, filter_query: dict[str, Any] | None = None) -> int:
        return await self._collection.count_documents(filter_query or {})

    async def find(
        self,
        filter_query: dict[str, Any],
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobModel]:
        cursor = self._collection.find(filter_query).skip(skip).limit(limit)
        jobs: list[JobModel] = []
        async for doc in cursor:
            jobs.append(_doc_to_model(doc))
        return jobs

    # ── Job-specific methods ───────────────────────────────────────────────

    async def find_by_fingerprint(self, fingerprint: str) -> JobModel | None:
        doc = await self._collection.find_one({"fingerprint": fingerprint})
        if doc is None:
            return None
        return _doc_to_model(doc)

    async def fingerprint_exists(self, fingerprint: str) -> bool:
        count = await self._collection.count_documents({"fingerprint": fingerprint})
        return count > 0

    async def find_by_source(
        self,
        source: JobSource,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobModel]:
        return await self.find({"source": source.value}, skip=skip, limit=limit)

    async def find_by_status(
        self,
        status: JobStatus,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[JobModel]:
        return await self.find({"status": status.value}, skip=skip, limit=limit)

    async def update_status(self, job_id: str, status: JobStatus) -> bool:
        result = await self._collection.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"status": status.value}},
        )
        return result.modified_count > 0

    async def update_classification(self, job_id: str, classification: dict) -> bool:
        result = await self._collection.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "classification": classification,
                    "status": JobStatus.CLASSIFIED.value,
                }
            },
        )
        return result.modified_count > 0

    async def update_jd_analysis(self, job_id: str, analysis: dict) -> bool:
        result = await self._collection.update_one(
            {"_id": ObjectId(job_id)},
            {
                "$set": {
                    "jd_analysis": analysis,
                    "status": JobStatus.ANALYZED.value,
                }
            },
        )
        return result.modified_count > 0

    async def bulk_create(self, jobs: list[JobModel]) -> int:
        """
        Insert multiple jobs, skipping duplicates by fingerprint.

        Uses ordered=False to continue inserting even if some fail (duplicates).
        """
        if not jobs:
            return 0

        docs = [_model_to_doc(job) for job in jobs]

        try:
            result = await self._collection.insert_many(docs, ordered=False)
            inserted = len(result.inserted_ids)
            logger.info("jobs_bulk_created", inserted=inserted, total=len(jobs))
            return inserted
        except BulkWriteError as bwe:
            # Some inserts succeeded, some were duplicates
            inserted = bwe.details.get("nInserted", 0)
            logger.info(
                "jobs_bulk_created_with_dupes",
                inserted=inserted,
                duplicates=len(jobs) - inserted,
            )
            return inserted
        except Exception as exc:
            raise DatabaseError(f"Bulk job insert failed: {exc}")
