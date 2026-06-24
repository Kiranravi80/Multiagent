from app.database import db


async def get_profile(email: str):

    user = await db.users.find_one(
        {"email": email}
    )

    if not user:
        return None

    user["id"] = str(user["_id"])

    del user["_id"]
    del user["password"]

    return user


async def update_profile(
    email: str,
    update_data: dict
):

    await db.users.update_one(
        {"email": email},
        {"$set": update_data}
    )

    return await get_profile(email)