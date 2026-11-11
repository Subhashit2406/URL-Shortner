import asyncio
import os
import sys
import hashlib

# Add parent directory to sys.path for app module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from app.database import engine, Base, AsyncSessionLocal
from app.models import Link, ClickEvent


async def main():
    print("=== Module 02 Database Seed & Query Verification ===")

    # Create tables if they do not exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("[1] Database schema created/verified.")

    async with AsyncSessionLocal() as session:
        # Seed test link
        test_code = "demo-link-99"
        test_url = "https://example.com/system-design-fundamentals"

        # Clean up existing test link if any
        stmt = select(Link).where(Link.code == test_code)
        result = await session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            await session.delete(existing)
            await session.commit()

        # Insert new link
        new_link = Link(
            code=test_code,
            long_url=test_url,
            created_by="instructor-test-user"
        )
        session.add(new_link)
        await session.commit()
        await session.refresh(new_link)
        print(f"[2] Inserted Link: id={new_link.id}, code={new_link.code}")

        # Record click event
        ip_hash = hashlib.sha256(b"127.0.0.1").hexdigest()
        click = ClickEvent(
            link_id=new_link.id,
            user_agent="Mozilla/5.0 (Windows NT 10.0)",
            referrer="https://google.com",
            ip_hash=ip_hash
        )
        session.add(click)
        await session.commit()
        print(f"[3] Inserted ClickEvent for link_id={new_link.id}")

        # Query by code (Fast Indexed Lookup)
        query_stmt = select(Link).where(Link.code == test_code)
        query_res = await session.execute(query_stmt)
        found_link = query_res.scalar_one_or_none()

        if found_link:
            print(f"[4] Query-by-code SUCCESS:")
            print(f"    - Requested Code: {test_code}")
            print(f"    - Selected Code:  {found_link.code}")
            print(f"    - Matched URL:    {found_link.long_url}")
            print(f"    - Created By:     {found_link.created_by}")
        else:
            print("[4] Query-by-code FAILED: Link not found!")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
