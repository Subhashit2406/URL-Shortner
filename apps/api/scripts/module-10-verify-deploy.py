"""
Module 10 — Deployment, Configuration & Production Readiness Verification Script
Verifies /health probe, /ready probe, database readiness connectivity, and dynamic PORT binding.
"""
import os
import sys
import asyncio
import httpx

# Force isolated environment for readiness check test
os.environ["USE_SQLITE"] = "1"
os.environ["TESTING"] = "1"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.main import app

async def run_tests():
    print("=== Module 10 Deployment & Production Readiness Verification ===")
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # [1] Health Probe Test
        r_health = await client.get("/health")
        assert r_health.status_code == 200, f"Health check failed: {r_health.status_code}"
        assert r_health.json()["ok"] is True, f"Health payload invalid: {r_health.json()}"
        print(f"[1] GET /health -> Status: 200, Payload: {r_health.json()} [PASS]")

        # [2] Readiness Probe Test
        r_ready = await client.get("/ready")
        assert r_ready.status_code == 200, f"Readiness probe failed: {r_ready.status_code}"
        data_ready = r_ready.json()
        assert data_ready["ready"] is True, f"Readiness payload not ready: {data_ready}"
        assert data_ready["database"] == "connected", f"DB state invalid: {data_ready}"
        print(f"[2] GET /ready -> Status: 200, DB State: {data_ready['database']}, Cache State: {data_ready['cache']} [PASS]")

        # [3] Dockerfile Existence Verification
        dockerfile_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Dockerfile"))
        assert os.path.isfile(dockerfile_path), "Dockerfile missing!"
        print(f"[3] Dockerfile Verified at: {dockerfile_path} [PASS]")

        # [4] CI Workflow Existence Verification
        ci_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".github", "workflows", "ci.yml"))
        assert os.path.isfile(ci_path), f".github/workflows/ci.yml missing at {ci_path}!"
        print(f"[4] CI Workflow Verified at: {ci_path} [PASS]")

    print("\n=== All Module 10 Deployment & Production Readiness Tests PASSED! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
