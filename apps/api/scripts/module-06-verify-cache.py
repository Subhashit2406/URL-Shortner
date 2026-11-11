import asyncio
import os
import sys
from httpx import AsyncClient, ASGITransport

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.database import init_db
from app.main import app
from app.services.cache_service import set_redirect_cache, get_redirect_cache, invalidate_redirect_cache, check_redirect_rate_limit


async def main():
    print("=== Module 06 Caching, Invalidation & Rate Limiting Verification ===")
    await init_db()

    headers = {"X-API-Key": settings.admin_api_key}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 1. Health Check
        health_resp = await client.get("/health")
        print(f"[1] GET /health -> Status: {health_resp.status_code} [EXPECTED: 200]")
        assert health_resp.status_code == 200

        # 2. Create link for testing
        create_resp = await client.post(
            "/links",
            json={"long_url": "https://example.com/original-target"},
            headers=headers
        )
        print(f"[2] POST /links -> Status: {create_resp.status_code} [EXPECTED: 201]")
        assert create_resp.status_code == 201
        created_data = create_resp.json()
        link_id = created_data["id"]
        code = created_data["code"]
        print(f"    - Link ID: {link_id}")
        print(f"    - Code:    {code}")

        # 3. First Redirect (Cache Miss -> Sets Cache)
        r1 = await client.get(f"/r/{code}", follow_redirects=False)
        print(f"[3] First GET /r/{code} (Cache Miss -> Set) -> Status: {r1.status_code}, Location: {r1.headers.get('location')}")
        assert r1.status_code == 307
        assert r1.headers.get("location") == "https://example.com/original-target"

        # Direct cache check
        cached_val = await get_redirect_cache(code)
        print(f"    - Cached value in Redis: '{cached_val}'")

        # 4. Second Redirect (Cache Hit)
        r2 = await client.get(f"/r/{code}", follow_redirects=False)
        print(f"[4] Second GET /r/{code} (Cache Hit) -> Status: {r2.status_code}, Location: {r2.headers.get('location')}")
        assert r2.status_code == 307
        assert r2.headers.get("location") == "https://example.com/original-target"

        # 5. Link Target Update -> Invalidates Cache
        update_resp = await client.patch(
            f"/links/{link_id}",
            json={"long_url": "https://example.org/updated-target"},
            headers=headers
        )
        print(f"[5] PATCH /links/{link_id} -> Status: {update_resp.status_code} [EXPECTED: 200]")
        assert update_resp.status_code == 200

        # Verify cache invalidation
        cached_val_after_update = await get_redirect_cache(code)
        print(f"    - Cached value after update (should be None): '{cached_val_after_update}'")

        # Third Redirect (Must return UPDATED target)
        r3 = await client.get(f"/r/{code}", follow_redirects=False)
        print(f"[6] Third GET /r/{code} after update -> Status: {r3.status_code}, Location: {r3.headers.get('location')}")
        assert r3.status_code == 307
        assert r3.headers.get("location") == "https://example.org/updated-target"

        # 6. Rate Limiting Test
        print("\n--- Running Rate Limiting Simulation ---")
        test_ip = "192.168.1.100"
        throttled = False
        for i in range(1, 70):
            allowed = await check_redirect_rate_limit(test_ip, max_requests=10, window_seconds=60)
            if not allowed:
                throttled = True
                print(f"    - Throttled successfully at request #{i} (Exceeded 10 req/min limit)")
                break
        assert throttled, "Rate limiting did not trigger!"

        print("\n=== All Module 06 Caching, Invalidation & Rate Limiting Tests PASSED! ===")


if __name__ == "__main__":
    asyncio.run(main())
