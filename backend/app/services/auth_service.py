from app.database import db
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token
)

async def register_user(user_data):

    existing_user = await db.users.find_one(
        {"email": user_data["email"]}
    )

    if existing_user:
        return None

    user_data["password"] = hash_password(
        user_data["password"]
    )

    result = await db.users.insert_one(
        user_data
    )

    return str(result.inserted_id)


async def login_user(email, password):

    user = await db.users.find_one(
        {"email": email}
    )

    if not user:
        return None

    if not verify_password(
        password,
        user["password"]
    ):
        return None

    token = create_access_token(
        {
            "user_id": str(user["_id"]),
            "email": user["email"]
        }
    )

    return token