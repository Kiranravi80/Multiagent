"""
MongoDB User Repository.

Concrete implementation of UserRepository for MongoDB via Motor.
All BSON/ObjectId conversions are handled internally.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.exceptions import DatabaseError, DuplicateEntityError
from app.core.logging import get_logger
from app.domain.models.user import UserModel
from app.domain.repositories.user_repository import UserRepository

logger = get_logger(__name__)


def _doc_to_model(doc: dict[str, Any]) -> UserModel:
    """Convert a MongoDB document to a UserModel."""
    doc["id"] = str(doc.pop("_id"))
    return UserModel.model_validate(doc)


def _model_to_doc(model: UserModel) -> dict[str, Any]:
    """Convert a UserModel to a MongoDB document."""
    data = model.model_dump(exclude={"id"})
    return data


class MongoUserRepository(UserRepository):
    """MongoDB implementation of the User repository."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    async def get_by_id(self, entity_id: str) -> UserModel | None:
        try:
            doc = await self._collection.find_one({"_id": ObjectId(entity_id)})
        except Exception as exc:
            logger.error("user_get_by_id_failed", user_id=entity_id, error=str(exc))
            raise DatabaseError(f"Failed to get user: {exc}")

        if doc is None:
            return None
        return _doc_to_model(doc)

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = None,
        sort_order: int = -1,
    ) -> list[UserModel]:
        cursor = self._collection.find().skip(skip).limit(limit)

        if sort_by:
            cursor = cursor.sort(sort_by, sort_order)

        users: list[UserModel] = []
        async for doc in cursor:
            users.append(_doc_to_model(doc))
        return users

    async def create(self, entity: UserModel) -> str:
        doc = _model_to_doc(entity)
        doc["created_at"] = datetime.now(UTC)
        doc["updated_at"] = datetime.now(UTC)

        try:
            result = await self._collection.insert_one(doc)
            logger.info("user_created", user_id=str(result.inserted_id))
            return str(result.inserted_id)
        except Exception as exc:
            if "duplicate key" in str(exc).lower():
                raise DuplicateEntityError("User", field="email", value=entity.email)
            raise DatabaseError(f"Failed to create user: {exc}")

    async def update(self, entity_id: str, data: dict[str, Any]) -> UserModel | None:
        data["updated_at"] = datetime.now(UTC)

        try:
            await self._collection.update_one(
                {"_id": ObjectId(entity_id)},
                {"$set": data},
            )
        except Exception as exc:
            raise DatabaseError(f"Failed to update user: {exc}")

        return await self.get_by_id(entity_id)

    async def delete(self, entity_id: str) -> bool:
        try:
            result = await self._collection.delete_one({"_id": ObjectId(entity_id)})
            return result.deleted_count > 0
        except Exception as exc:
            raise DatabaseError(f"Failed to delete user: {exc}")

    async def count(self, filter_query: dict[str, Any] | None = None) -> int:
        return await self._collection.count_documents(filter_query or {})

    async def find(
        self,
        filter_query: dict[str, Any],
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> list[UserModel]:
        cursor = self._collection.find(filter_query).skip(skip).limit(limit)
        users: list[UserModel] = []
        async for doc in cursor:
            users.append(_doc_to_model(doc))
        return users

    # ── User-specific methods ──────────────────────────────────────────────

    async def find_by_email(self, email: str) -> UserModel | None:
        doc = await self._collection.find_one({"email": email})
        if doc is None:
            return None
        return _doc_to_model(doc)

    async def email_exists(self, email: str) -> bool:
        count = await self._collection.count_documents({"email": email})
        return count > 0

    async def update_profile(self, email: str, profile_data: dict) -> UserModel | None:
        profile_data["updated_at"] = datetime.now(UTC)

        await self._collection.update_one(
            {"email": email},
            {"$set": profile_data},
        )
        return await self.find_by_email(email)

    async def update_career_analysis(self, user_id: str, analysis: dict) -> bool:
        result = await self._collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"career_analysis": analysis, "updated_at": datetime.now(UTC)}},
        )
        return result.modified_count > 0

    async def update_resume_data(
        self,
        user_id: str,
        *,
        resume_text: str = "",
        file_path: str = "",
        parsed_data: dict | None = None,
    ) -> bool:
        update: dict[str, Any] = {"updated_at": datetime.now(UTC)}

        if resume_text:
            update["resume_text"] = resume_text
        if file_path:
            update["resume_file_path"] = file_path
        if parsed_data:
            for key, value in parsed_data.items():
                update[key] = value

        result = await self._collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update},
        )
        return result.modified_count > 0
