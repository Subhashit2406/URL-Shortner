import asyncio
import os
import sys
from httpx import AsyncClient, ASGITransport

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.database import init_db
from app.main import app


async def main():
    print("=== Module 04 API Key Authentication Boundary Verification ===")
    await init_db()
    print(f"Configured ADMIN_API_KEY: '{settings.admin_api_key}'")

    valid_headers = {"X-API-Key": settings.admin_api_key}
    invalid_headers = {"X-API-Key": "invalid_wrong_secret_key"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 1. Health check remains public
        health_resp = await client.get("/health")
        print(f"[1] GET /health (No Auth) -> Status: {health_resp.status_code} [EXPECTED: 200]")
        assert health_resp.status_code == 200, f"Expected 200, got {health_resp.status_code}"

        # 2. GET /links without API key -> 401
        no_auth_list = await client.get("/links")
        print(f"[2] GET /links (No Auth) -> Status: {no_auth_list.status_code} [EXPECTED: 401]")
        assert no_auth_list.status_code == 401, f"Expected 401, got {no_auth_list.status_code}"

        # 3. GET /links with invalid API key -> 401
        bad_auth_list = await client.get("/links", headers=invalid_headers)
        print(f"[3] GET /links (Invalid API Key) -> Status: {bad_auth_list.status_code} [EXPECTED: 401]")
        assert bad_auth_list.status_code == 401, f"Expected 401, got {bad_auth_list.status_code}"

        # 4. POST /links without API key -> 401
        no_auth_create = await client.post("/links", json={"long_url": "https://example.com/protected"})
        print(f"[4] POST /links (No Auth) -> Status: {no_auth_create.status_code} [EXPECTED: 401]")
        assert no_auth_create.status_code == 401, f"Expected 401, got {no_auth_create.status_code}"

        # 5. POST /links with valid API key -> 201
        valid_create = await client.post(
            "/links",
            json={"long_url": "https://example.com/protected"},
            headers=valid_headers
        )
        print(f"[5] POST /links (Valid API Key) -> Status: {valid_create.status_code} [EXPECTED: 201]")
        assert valid_create.status_code == 201, f"Expected 201, got {valid_create.status_code}"
        created_data = valid_create.json()
        code = created_data["code"]
        link_id = created_data["id"]
        print(f"    - Created ID:   {link_id}")
        print(f"    - Created Code: {code}")

        # 6. GET /links with valid API key -> 200
        valid_list = await client.get("/links", headers=valid_headers)
        print(f"[6] GET /links (Valid API Key) -> Status: {valid_list.status_code} [EXPECTED: 200]")
        assert valid_list.status_code == 200, f"Expected 200, got {valid_list.status_code}"

        # 7. GET /links/{id} with valid API key -> 200
        valid_get = await client.get(f"/links/{link_id}", headers=valid_headers)
        print(f"[7] GET /links/{link_id} (Valid API Key) -> Status: {valid_get.status_code} [EXPECTED: 200]")
        assert valid_get.status_code == 200, f"Expected 200, got {valid_get.status_code}"

        # 8. GET /links/{id} without API key -> 401
        no_auth_get = await client.get(f"/links/{link_id}")
        print(f"[8] GET /links/{link_id} (No Auth) -> Status: {no_auth_get.status_code} [EXPECTED: 401]")
        assert no_auth_get.status_code == 401, f"Expected 401, got {no_auth_get.status_code}"

        # 9. Public redirect GET /r/{code} remains public -> 307
        redirect_resp = await client.get(f"/r/{code}", follow_redirects=False)
        print(f"[9] GET /r/{code} (No Auth Public Redirect) -> Status: {redirect_resp.status_code} [EXPECTED: 307]")
        assert redirect_resp.status_code == 307, f"Expected 307, got {redirect_resp.status_code}"
        assert redirect_resp.headers.get("location") == "https://example.com/protected"

        print("\n=== All Module 04 Authentication Boundary Tests PASSED! ===")


if __name__ == "__main__":
    asyncio.run(main())
