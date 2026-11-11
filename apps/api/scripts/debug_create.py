import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import AsyncSessionLocal
from app.schemas.link import LinkCreate
from app.services.links_service import create_link

async def test():
    try:
        async with AsyncSessionLocal() as session:
            res = await create_link(session, LinkCreate(long_url="https://example.com"))
            print("SUCCESS:", res)
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
