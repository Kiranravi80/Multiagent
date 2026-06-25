"""MongoDB Portfolio Repository."""

from __future__ import annotations

from typing import Any

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.exceptions import DatabaseError
from app.core.logging import get_logger
from app.domain.models.portfolio import PortfolioModel
from app.domain.repositories.portfolio_repository import PortfolioRepository

logger = get_logger(__name__)


def _doc_to_model(doc: dict[str, Any]) -> PortfolioModel:
    doc["id"] = str(doc.pop("_id"))
    return PortfolioModel.model_validate(doc)


class MongoPortfolioRepository(PortfolioRepository):
    """MongoDB implementation of PortfolioRepository."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    async def get_by_id(self, entity_id: str) -> PortfolioModel | None:
        doc = await self._collection.find_one({"_id": ObjectId(entity_id)})
        return _doc_to_model(doc) if doc else None

    async def get_by_user_id(self, user_id: str) -> PortfolioModel | None:
        doc = await self._collection.find_one({"user_id": user_id})
        return _doc_to_model(doc) if doc else None

    async def get_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        sort_by: str | None = "updated_at",
        sort_order: int = -1,
    ) -> list[PortfolioModel]:
        cursor = self._collection.find().skip(skip).limit(limit)
        if sort_by:
            cursor = cursor.sort(sort_by, sort_order)
        return [_doc_to_model(doc) async for doc in cursor]

    async def create(self, entity: PortfolioModel) -> str:
        doc = entity.to_dict()
        if "_id" in doc:
            doc.pop("_id")
        try:
            result = await self._collection.insert_one(doc)
            return str(result.inserted_id)
        except Exception as exc:
            raise DatabaseError(f"Failed to create portfolio entry: {exc}")

    async def update(self, entity_id: str, data: dict[str, Any]) -> PortfolioModel | None:
        try:
            await self._collection.update_one(
                {"_id": ObjectId(entity_id)},
                {"$set": data}
            )
            return await self.get_by_id(entity_id)
        except Exception as exc:
            raise DatabaseError(f"Failed to update portfolio: {exc}")

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
    ) -> list[PortfolioModel]:
        cursor = self._collection.find(filter_query).skip(skip).limit(limit)
        return [_doc_to_model(doc) async for doc in cursor]
