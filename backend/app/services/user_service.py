from bson import ObjectId
from app.database import db


async def create_user(user_data: dict):
    result = await db.users.insert_one(user_data)
    return str(result.inserted_id)


async def get_users():
    users = []

    async for user in db.users.find():
        user["id"] = str(user["_id"])
        del user["_id"]
        users.append(user)

    return users


async def get_user(user_id: str):
    user = await db.users.find_one({"_id": ObjectId(user_id)})

    if not user:
        return None

    user["id"] = str(user["_id"])
    del user["_id"]

    return user


async def update_user(user_id: str, update_data: dict):
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )

    return await get_user(user_id)


async def delete_user(user_id: str):
    result = await db.users.delete_one(
        {"_id": ObjectId(user_id)}
    )

    return result.deleted_count > 0