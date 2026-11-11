import asyncio
import os
import sys
import httpx

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import init_db

API_KEY = "dev_admin_api_key_secret_123"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


async def main():
    print("=== Module 08 Safe & Predictable Search Verification ===")
    await init_db()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Health check
        res_health = await client.get("/health")
        print(f"[1] GET /health -> Status: {res_health.status_code} [EXPECTED: 200]")
        assert res_health.status_code == 200

        # 2. Seed test links
        links_to_create = [
            "https://example.com/system-design-search-query",
            "https://example.org/database-index-optimization",
            "https://test.io/caching-redis-layer"
        ]
        created_codes = []
        for url in links_to_create:
            res_create = await client.post("/links", json={"long_url": url}, headers=HEADERS)
            assert res_create.status_code == 201
            created_codes.append(res_create.json()["code"])
        print(f"[2] Seeded 3 test links: {created_codes}")

        # 3. Test Keyword Search (q=system-design)
        res_search_kw = await client.get("/links/search?q=system-design", headers=HEADERS)
        print(f"[3] GET /links/search?q=system-design -> Status: {res_search_kw.status_code} [EXPECTED: 200]")
        assert res_search_kw.status_code == 200
        search_kw_data = res_search_kw.json()
        print(f"    - Matching Total Items: {search_kw_data['total']} [EXPECTED >= 1]")
        assert search_kw_data["total"] >= 1
        assert any("system-design" in item["long_url"] for item in search_kw_data["items"])

        # 4. Test Sorting (sort_by=code, order=asc)
        res_search_sort = await client.get("/links/search?sort_by=code&order=asc", headers=HEADERS)
        print(f"[4] GET /links/search?sort_by=code&order=asc -> Status: {res_search_sort.status_code} [EXPECTED: 200]")
        assert res_search_sort.status_code == 200
        sort_items = res_search_sort.json()["items"]
        codes = [item["code"] for item in sort_items]
        assert codes == sorted(codes), f"Codes not sorted ascending: {codes}"
        print(f"    - Codes verified ascending: {codes}")

        # 5. Bounded Pagination Security Test (page_size = 500 > 100 limit)
        res_page_size_bound = await client.get("/links/search?page_size=500", headers=HEADERS)
        print(f"[5] GET /links/search?page_size=500 -> Status: {res_page_size_bound.status_code} [EXPECTED: 422 REJECTED]")
        assert res_page_size_bound.status_code == 422, "page_size > 100 MUST be rejected with HTTP 422!"

        # 6. Parameter Allowlisting Security Test (sort_by = invalid_column)
        res_invalid_sort = await client.get("/links/search?sort_by=invalid_column;DROP", headers=HEADERS)
        print(f"[6] GET /links/search?sort_by=invalid_column -> Status: {res_invalid_sort.status_code} [EXPECTED: 422 REJECTED]")
        assert res_invalid_sort.status_code == 422, "Invalid sort_by parameter MUST be rejected with HTTP 422!"

        # 7. Unauthenticated Request Security Test
        res_unauth = await client.get("/links/search?q=test")
        print(f"[7] GET /links/search (Unauthenticated) -> Status: {res_unauth.status_code} [EXPECTED: 401 UNAUTHORIZED]")
        assert res_unauth.status_code == 401

    print("\n=== All Module 08 Safe & Predictable Search Tests PASSED! ===")


if __name__ == "__main__":
    asyncio.run(main())
