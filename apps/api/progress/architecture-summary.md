# Project Architecture Summary

## 1. Directory & Folder Structure
- `apps/api/app/`: Primary application source code containing route controllers, ORM models, Pydantic schemas, and middleware.
- `apps/api/app/routers/`: Modular route handlers (`links.py`, `redirect.py`).
- `apps/api/scripts/`: Automated regression and module verification scripts (`module-03` through `module-10`).
- `apps/api/tests/`: Automated pytest integration test suite.
- `.github/workflows/`: Production CI pipeline (`ci.yml`).

## 2. Key Data Models
- **Link (`Link`)**: Represents shortened links with fields `id` (UUID), `original_url` (Text), `short_code` (String, indexed), `created_at` (DateTime), `created_by` (String), `is_active` (Boolean).
- **ClickEvent (`ClickEvent`)**: Represents click analytics with fields `id` (UUID), `click_id` (String, unique idempotency key), `link_id` (UUID FK), `timestamp` (DateTime), `ip_hash` (String 64-char SHA-256 digest), `user_agent` (Text).

## 3. API Routes & Endpoints
- `GET /health`: Public liveness health probe returning HTTP 200 process status.
- `GET /ready`: Public readiness probe verifying database (PostgreSQL/SQLite) and Redis ping connectivity.
- `POST /links`: Administrative endpoint creating shortened URLs (requires `X-API-Key`).
- `GET /links`: Administrative endpoint listing shortened URLs (requires `X-API-Key`).
- `GET /links/search`: Administrative parameterized search endpoint (`q`, `sort_by`, `order`, `page`, `page_size <= 100`).
- `GET /r/{short_code}`: Public high-throughput redirect endpoint utilizing Cache-Aside pattern (Redis -> DB fallback).
- `GET /links/{link_id}/analytics`: Administrative endpoint returning aggregated click metrics.
- `DELETE /links/analytics/purge`: Administrative endpoint purging click events older than `retention_days`.

## 4. Authentication Mechanism
- Header-based administrative authentication enforced by FastAPI Dependency Injection (`get_admin_api_key`) validating `X-API-Key` against `ADMIN_API_KEY` setting. Public endpoints (`/health`, `/ready`, `/r/{code}`) bypass auth by design.

## 5. Database & Cache Technology
- Primary Database: PostgreSQL 16 (via async SQLAlchemy 2.0 and `asyncpg`) with SQLite (`aiosqlite`) fallback when `USE_SQLITE=1`.
- Caching & Rate Limiting: Redis (`redis.asyncio`) backing Cache-Aside lookups and sliding-window rate limit counters.

## 6. Extension Points
- **Routes**: Add new file under `apps/api/app/routers/` and register in `app/main.py`.
- **Data Models**: Add SQLAlchemy model in `apps/api/app/models.py`.
- **Schemas**: Add Pydantic validation schema under `apps/api/app/schemas/`.
- **Background Tasks**: Dispatch background tasks in `app/routers/redirect.py` or separate worker handlers.
