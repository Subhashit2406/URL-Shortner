import asyncio
import io
import logging
import os
import sys
from httpx import AsyncClient, ASGITransport

# Add parent directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.main import app


async def main():
    print("=== Module 05 Error Handling & Secret Redaction Verification ===")

    # Capture log output to verify secret redaction
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    logging.getLogger("upsk_api").addHandler(handler)
    logging.getLogger("upsk_api").setLevel(logging.INFO)

    valid_headers = {"X-API-Key": settings.admin_api_key}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:

        # 1. GET /health returns 200
        health_resp = await client.get("/health")
        print(f"[1] GET /health -> Status: {health_resp.status_code} [EXPECTED: 200]")
        assert health_resp.status_code == 200, f"Expected 200, got {health_resp.status_code}"

        # 2. Unauthenticated GET /links returns 401 with error envelope
        unauth_resp = await client.get("/links")
        print(f"[2] GET /links (Unauthenticated) -> Status: {unauth_resp.status_code} [EXPECTED: 401]")
        assert unauth_resp.status_code == 401, f"Expected 401, got {unauth_resp.status_code}"
        unauth_json = unauth_resp.json()
        assert "error" in unauth_json, "Response missing 'error' key"
        assert unauth_json["error"]["code"] == "UNAUTHORIZED", f"Expected code UNAUTHORIZED, got {unauth_json['error']['code']}"
        assert unauth_json["error"]["message"] == "Missing API key"
        assert "request_id" in unauth_json["error"], "Missing request_id in error envelope"
        assert unauth_resp.headers.get("X-Request-ID") == unauth_json["error"]["request_id"]
        print(f"    - Error envelope code:       {unauth_json['error']['code']}")
        print(f"    - Error envelope request_id: {unauth_json['error']['request_id']}")

        # 3. Authenticated invalid validation request: POST /links with "long_url": "not-a-url"
        invalid_body_resp = await client.post(
            "/links",
            json={"long_url": "not-a-url"},
            headers=valid_headers
        )
        print(f"[3] POST /links (Invalid Body) -> Status: {invalid_body_resp.status_code} [EXPECTED: 422]")
        assert invalid_body_resp.status_code == 422, f"Expected 422, got {invalid_body_resp.status_code}"
        val_json = invalid_body_resp.json()
        assert "error" in val_json
        assert val_json["error"]["code"] == "VALIDATION_ERROR"
        assert val_json["error"]["message"] == "Request validation failed"
        assert "request_id" in val_json["error"]
        # Verify no stack trace or database details leaked
        raw_body_text = invalid_body_resp.text
        assert "Traceback" not in raw_body_text
        assert "sqlalchemy" not in raw_body_text.lower()
        print(f"    - 422 envelope verified safe without stack traces.")

        # 4. Unexpected server error test (GET /_test/raise-500)
        err_500_resp = await client.get("/_test/raise-500")
        print(f"[4] GET /_test/raise-500 -> Status: {err_500_resp.status_code} [EXPECTED: 500]")
        assert err_500_resp.status_code == 500, f"Expected 500, got {err_500_resp.status_code}"
        err_500_json = err_500_resp.json()
        assert "error" in err_500_json
        assert err_500_json["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert err_500_json["error"]["message"] == "An unexpected server error occurred"
        assert "request_id" in err_500_json["error"]
        assert "Traceback" not in err_500_resp.text
        assert "Simulated unexpected server error" not in err_500_resp.text
        print(f"    - 500 envelope verified safe without leaking internal error text.")

        # 5. Secret redaction test
        secret_header_val = "DO_NOT_LOG_ME_SECRET_12345"
        secret_test_resp = await client.get("/links", headers={"X-API-Key": secret_header_val})
        print(f"[5] Secret Redaction Test -> Status: {secret_test_resp.status_code} [EXPECTED: 401]")
        assert secret_test_resp.status_code == 401
        log_content = log_capture.getvalue()
        assert secret_header_val not in log_content, f"SECRET LEAK DETECTED IN SERVER LOGS!"
        print(f"    - Secret header '{secret_header_val}' verified NOT present in server logs.")

        print("\n=== All Module 05 Error Handling Tests PASSED! ===")


if __name__ == "__main__":
    asyncio.run(main())
