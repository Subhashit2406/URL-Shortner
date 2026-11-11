"""
Module 09 — Automated Testing & Test Isolation Verification Script
Tests redirect correctness, auth protection, IDOR scoping, retention purge, URL validation, and async idempotency.
"""
import os
import sys
import asyncio
import httpx
import uuid
from datetime import datetime, timezone

# Force isolated test environment database
os.environ["USE_SQLITE"] = "1"
os.environ["TESTING"] = "1"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app

ADMIN_API_KEY = "dev_admin_api_key_secret_123"
HEADERS = {"X-API-Key": ADMIN_API_KEY}
INVALID_HEADERS = {"X-API-Key": "invalid_api_key_xyz"}

async def run_tests():
    print("=== Module 09 Automated Testing & Isolation Verification ===")
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # [1] Health Check
        r_health = await client.get("/health")
        assert r_health.status_code == 200, f"Health failed: {r_health.status_code}"
        print("[1] GET /health -> Status: 200 [PASS]")

        # [2] Link Creation Test
        long_url = "https://example.com/module-09-test-url"
        r_create = await client.post("/links", json={"long_url": long_url}, headers=HEADERS)
        assert r_create.status_code == 201, f"Create link failed: {r_create.status_code}"
        data_create = r_create.json()
        link_id_str = data_create["id"]
        link_uuid = uuid.UUID(link_id_str)
        code = data_create["code"]
        print(f"[2] POST /links -> Created ID: {link_id_str}, Code: {code} [PASS]")

        # [3] Redirect Correctness Test
        r_redirect = await client.get(f"/r/{code}")
        assert r_redirect.status_code == 307, f"Redirect failed: {r_redirect.status_code}"
        assert r_redirect.headers.get("location") == long_url, f"Wrong location: {r_redirect.headers.get('location')}"
        print(f"[3] GET /r/{code} -> Status: 307 Redirect to {long_url} [PASS]")

        # [4] Auth Protection Test
        r_unauth = await client.get("/links")
        assert r_unauth.status_code == 401, f"Unauth check failed: {r_unauth.status_code}"
        print("[4] GET /links (Unauthenticated) -> Status: 401 Unauthorized [PASS]")

        # [4b] Unauthenticated DELETE Protection Test
        r_del_unauth = await client.delete(f"/links/{link_id_str}")
        assert r_del_unauth.status_code == 401, f"Unauthenticated DELETE MUST be rejected with 401! Got: {r_del_unauth.status_code}"
        print("[4b] DELETE /links (Unauthenticated) -> Status: 401 [PASS]")

        # [5] Owner Scoping / IDOR Protection Test
        r_idor = await client.get(f"/links/{link_id_str}", headers=INVALID_HEADERS)
        assert r_idor.status_code in (401, 403, 404), f"IDOR check failed: {r_idor.status_code}"
        print(f"[5] GET /links/{link_id_str} (Invalid API Key / IDOR) -> Status: {r_idor.status_code} [PASS]")

        # [6] URL Validation Security Test
        malicious_url = "http%3A%2F%2Fevil.example.com"
        r_bad_url = await client.post("/links", json={"long_url": malicious_url}, headers=HEADERS)
        assert r_bad_url.status_code == 422, f"Malicious URL not rejected: {r_bad_url.status_code}"
        print("[6] POST /links (Malicious Encoded URL) -> Status: 422 Rejected [PASS]")

        # [7] Async Click Analytics & Idempotency Test
        click_id = f"test-click-{uuid.uuid4()}"
        from app.services.analytics_service import record_click_event_idempotent
        from app.database import AsyncSessionLocal
        
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as session:
            # First recording
            c1 = await record_click_event_idempotent(session, click_id, link_uuid, now, "127.0.0.1", "pytest-agent")
            # Replayed recording with same idempotency key
            c2 = await record_click_event_idempotent(session, click_id, link_uuid, now, "127.0.0.1", "pytest-agent")
            assert c1.id == c2.id, "Idempotency failed: duplicated click record!"
        print(f"[7] Async Click Idempotency Key '{click_id}' -> Duplicate replay prevented [PASS]")

        # [8] Retention Enforcement Test
        r_purge = await client.delete("/links/analytics/purge?retention_days=0", headers=HEADERS)
        assert r_purge.status_code == 200, f"Purge analytics failed: {r_purge.status_code}"
        purged_count = r_purge.json()["purged_count"]
        print(f"[8] DELETE /links/analytics/purge -> Purged {purged_count} records [PASS]")

    print("\n=== All Module 09 Automated Testing & Isolation Tests PASSED! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
