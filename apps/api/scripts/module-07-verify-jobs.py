import asyncio
import os
import uuid
import sys
from datetime import datetime, timezone
import httpx

# Ensure app package is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import AsyncSessionLocal, init_db
from app.models import ClickEvent
from app.services.analytics_service import record_click_event_idempotent, purge_old_clicks
from sqlalchemy import select

API_KEY = "dev_admin_api_key_secret_123"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


async def main():
    print("=== Module 07 Async Background Jobs & Analytics Verification ===")
    await init_db()

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Health check
        res_health = await client.get("/health")
        print(f"[1] GET /health -> Status: {res_health.status_code} [EXPECTED: 200]")
        assert res_health.status_code == 200

        # 2. Create a short link
        link_payload = {"long_url": "https://example.com/system-design-jobs"}
        res_create = await client.post("/links", json=link_payload, headers=HEADERS)
        print(f"[2] POST /links -> Status: {res_create.status_code} [EXPECTED: 201]")
        assert res_create.status_code == 201
        link_data = res_create.json()
        link_id = link_data["id"]
        code = link_data["code"]
        print(f"    - Created Link ID: {link_id}")
        print(f"    - Created Code:    {code}")

        # 3. First Redirect (Trigger background click analytics job)
        r1 = await client.get(f"/r/{code}", follow_redirects=False)
        print(f"[3] First GET /r/{code} -> Status: {r1.status_code} [EXPECTED: 307]")
        assert r1.status_code == 307

        # 4. Second Redirect (Trigger background click analytics job)
        r2 = await client.get(f"/r/{code}", follow_redirects=False)
        print(f"[4] Second GET /r/{code} -> Status: {r2.status_code} [EXPECTED: 307]")
        assert r2.status_code == 307

        # Wait briefly for background tasks to complete processing
        await asyncio.sleep(0.5)

        # 5. Protected Analytics Query
        res_analytics = await client.get(
            f"/links/{link_id}/analytics?from=2000-01-01T00:00:00Z&to=2100-01-01T00:00:00Z",
            headers=HEADERS
        )
        print(f"[5] GET /links/{link_id}/analytics -> Status: {res_analytics.status_code} [EXPECTED: 200]")
        assert res_analytics.status_code == 200
        analytics_data = res_analytics.json()
        print(f"    - Total Clicks Counted: {analytics_data['total_clicks']} [EXPECTED: 2]")
        print(f"    - Last Clicked Timestamp: {analytics_data['last_clicked_at']}")
        assert analytics_data["total_clicks"] == 2
        assert analytics_data["last_clicked_at"] is not None

        # 6. Idempotency Proof (Replay duplicate click_id)
        print("\n--- Running Idempotency Simulation ---")
        duplicate_click_id = "test-idempotent-click-id-12345"
        async with AsyncSessionLocal() as session:
            # First execution
            first_event = await record_click_event_idempotent(
                session=session,
                click_id=duplicate_click_id,
                link_id=uuid.UUID(link_id),
                clicked_at=datetime.now(timezone.utc),
                ip_address="192.168.1.50"
            )
            # Second execution (Replay duplicate job)
            replay_event = await record_click_event_idempotent(
                session=session,
                click_id=duplicate_click_id,
                link_id=uuid.UUID(link_id),
                clicked_at=datetime.now(timezone.utc),
                ip_address="192.168.1.50"
            )
            assert first_event is not None
            assert replay_event is not None
            assert first_event.id == replay_event.id
            print(f"    [PASS] Duplicate click_id '{duplicate_click_id}' replayed safely without creating duplicate record!")

        # 7. Privacy Proof (IP Hashing verification)
        print("\n--- Running Privacy Verification ---")
        async with AsyncSessionLocal() as session:
            stmt = select(ClickEvent).where(ClickEvent.link_id == uuid.UUID(link_id))
            res_events = await session.execute(stmt)
            events = res_events.scalars().all()
            for evt in events:
                if evt.ip_hash:
                    assert len(evt.ip_hash) == 64, "ip_hash must be a 64-character SHA-256 string"
            print(f"    [PASS] IP Hashing Verified: All stored ip_hash entries are 64-character SHA-256 digests.")

        # 8. Retention Purge Proof
        print("\n--- Running Retention Purge Simulation ---")
        res_purge = await client.delete("/links/analytics/purge?retention_days=0", headers=HEADERS)
        print(f"[8] DELETE /links/analytics/purge?retention_days=0 -> Status: {res_purge.status_code} [EXPECTED: 200]")
        assert res_purge.status_code == 200
        purge_data = res_purge.json()
        print(f"    - Purged Count: {purge_data['purged_count']}")
        assert purge_data["purged_count"] >= 2

        # Re-verify analytics count after purge
        res_after_purge = await client.get(
            f"/links/{link_id}/analytics?from=2000-01-01T00:00:00Z&to=2100-01-01T00:00:00Z",
            headers=HEADERS
        )
        assert res_after_purge.json()["total_clicks"] == 0
        print("    [PASS] Analytics count after retention purge is 0!")

    print("\n=== All Module 07 Async Jobs, Idempotency & Analytics Tests PASSED! ===")


if __name__ == "__main__":
    asyncio.run(main())
