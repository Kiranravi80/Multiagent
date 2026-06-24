import asyncio
from database import client

async def test():
    result = await client.admin.command("ping")
    print("MongoDB Connected!")
    print(result)

asyncio.run(test())