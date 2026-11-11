import asyncio
import os
import sys
import json
from httpx import AsyncClient, ASGITransport

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.database import init_db
from app.main import app


async def main():
    print("=== Module 03 Core API & Security Abuse Verification ===")
    await init_db()
    headers = {"X-API-Key": settings.admin_api_key}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 1. Health Check
        health_resp = await client.get("/health")
        print(f"[1] GET /health -> Status: {health_resp.status_code}, Body: {health_resp.json()}")

        # 2. Valid Link Creation
        valid_payload = {"long_url": "https://example.com/system-design"}
        create_resp = await client.post("/links", json=valid_payload, headers=headers)
        print(f"[2] POST /links (Valid URL) -> Status: {create_resp.status_code}")
        assert create_resp.status_code == 201, f"Expected 201, got {create_resp.status_code}"
        created_data = create_resp.json()
        print(f"    - Created ID: {created_data['id']}")
        print(f"    - Code:       {created_data['code']}")
        print(f"    - Short URL:  {created_data['short_url']}")
        code = created_data['code']
        link_id = created_data['id']

        # 3. List Links
        list_resp = await client.get("/links", headers=headers)
        print(f"[3] GET /links -> Status: {list_resp.status_code}, Total Items: {list_resp.json()['total']}")

        # 4. Get Link by ID
        get_resp = await client.get(f"/links/{link_id}", headers=headers)
        print(f"[4] GET /links/{link_id} -> Status: {get_resp.status_code}, Matched Code: {get_resp.json()['code']}")

        # 5. Public Redirect (GET /r/{code})
        redirect_resp = await client.get(f"/r/{code}", follow_redirects=False)
        print(f"[5] GET /r/{code} -> Status: {redirect_resp.status_code}, Location: {redirect_resp.headers.get('location')}")
        assert redirect_resp.status_code == 307, f"Expected 307 redirect, got {redirect_resp.status_code}"
        assert redirect_resp.headers.get('location') == "https://example.com/system-design"

        # 6. Security Abuse Checks (Expect HTTP 400 or 422 Bad Request/Unprocessable Entity)
        print("\n--- Running 9 Security Abuse Checks (Expect HTTP 400/422 Rejection) ---")
        abuse_payloads = [
            ("javascript:alert(1)", "Basic XSS pseudo-scheme"),
            ("JaVaScRiPt:alert(1)", "Case-insensitive scheme bypass"),
            (" javascript:alert(1) ", "Leading/trailing whitespace padding"),
            ("data:text/html,<svg/onload=alert(1)>", "Data URI payload"),
            ("//evil.example.com", "Scheme-relative URL"),
            ("http:%2f%2fevil.example.com", "Encoded slashes"),
            ("http%3A%2F%2Fevil.example.com", "Encoded scheme"),
            ("http:\\\\evil.example.com", "Backslashes in domain host"),
            ("https://good.com@evil.example.com", "Userinfo credential embedding trick"),
        ]

        passed_abuse_checks = 0
        for payload_str, description in abuse_payloads:
            resp = await client.post("/links", json={"long_url": payload_str}, headers=headers)
            is_rejected = resp.status_code in (400, 422)
            status_tag = "[PASS]" if is_rejected else "[FAIL]"
            status_symbol = "REJECTED" if is_rejected else "ACCEPTED (FAILED!)"
            print(f"  {status_tag} Payload: '{payload_str[:35]}...' ({description}) -> Status: {resp.status_code} [{status_symbol}]")
            if is_rejected:
                passed_abuse_checks += 1

        print(f"\nAbuse Checks Summary: {passed_abuse_checks}/{len(abuse_payloads)} malicious payloads correctly blocked.")


if __name__ == "__main__":
    asyncio.run(main())
