# System Context & Per-Task Context Packages

## Strategy
- **Context Strategy**: Layered / Surgical Context Strategy (Architectural + Local + Negative Constraints)

---

## Part 1: System-Level Context Document

### Architecture Summary
- **Framework**: FastAPI (Python 3.11.9) with Uvicorn server.
- **ORM & Database**: Async SQLAlchemy 2.0 (`asyncpg` for PostgreSQL 16, `aiosqlite` fallback for SQLite).
- **Caching & Limits**: Redis (`redis.asyncio`) Cache-Aside lookups and sliding-window rate limiting.
- **Routing Structure**: Router controllers under `app/routers/` registered in `app/main.py`.

### Coding & Naming Conventions
- **Variables & Methods**: `snake_case` for variables, parameters, and functions.
- **Classes & Models**: `PascalCase` for Pydantic schemas and SQLAlchemy models.
- **File Names**: Lowercase `snake_case` (e.g., `app/models.py`, `app/routers/links.py`).

### Error Envelope Format
All error responses use standardized JSON envelope:
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing API key.",
    "request_id": "926c0d97-5dbc-4cba-b210-bf5456045373"
  }
}
```
HTTP Status Codes:
- `400 Bad Request`: Validation failure / anti-replay token reuse (`VALIDATION_ERROR`).
- `401 Unauthorized`: Missing or invalid `X-API-Key` (`UNAUTHORIZED`).
- `403 Forbidden`: Insufficient role permissions (`FORBIDDEN`).
- `404 Not Found`: Resource does not exist (`NOT_FOUND`).
- `422 Unprocessable Content`: Pydantic payload schema mismatch (`UNPROCESSABLE_ENTITY`).
- `500 Internal Server Error`: Unexpected runtime failure (`INTERNAL_ERROR`).

### Negative Constraints
- **Dependencies**: Do NOT introduce new external libraries or packages.
- **Auth Re-use**: Must use existing `get_admin_api_key` dependency; do NOT invent new auth schemes.
- **Schema Isolation**: New routers must register clean route prefixes (`/teams`, `/invites`).

---

## Part 2: Per-Task Context Bundles

### Bundle 1 (Task 1: Team & Member Data Models)
- **Files to Read**:
  1. `app/models.py` (Reason: Defines existing `Link` and `ClickEvent` ORM models. *If omitted*: Agent invents mismatched model declarations or legacy Sync SQLAlchemy patterns.)
  2. `app/database.py` (Reason: Defines `Base` declarative class and `get_db` session generator. *If omitted*: Agent creates a duplicate Base instance breaking migration metadata.)
- **Files to Modify**: `app/models.py`
- **Expected Output**: Declarative `Team` and `TeamMember` classes adhering to SQLAlchemy 2.0.

### Bundle 2 (Task 2: Team CRUD Endpoints)
- **Files to Read**:
  1. `app/models.py` (Reason: Provides `Team` and `TeamMember` schemas. *If omitted*: Agent invents non-existent model attributes.)
  2. `app/routers/links.py` (Reason: Provides reference router controller layout and exception handling. *If omitted*: Agent uses raw Starlette or Flask route syntax.)
  3. `app/main.py` (Reason: Shows `get_admin_api_key` auth dependency. *If omitted*: Agent leaves endpoints unauthenticated or invents JWT auth.)
- **Files to Modify**: `app/routers/teams.py`, `app/main.py`
- **Expected Output**: Clean APIRouter with `POST /teams` and `GET /teams/{id}` endpoints.

### Bundle 3 (Task 3: Team Invitation Model & Endpoints)
- **Files to Read**:
  1. `app/models.py` (Reason: Provides `TeamInvite` data structure. *If omitted*: Agent guesses column names for tokens and expiration.)
  2. `app/routers/teams.py` (Reason: Endpoint target for `POST /teams/{id}/invites`. *If omitted*: Agent puts invite logic in a standalone conflicting router.)
- **Files to Modify**: `app/models.py`, `app/routers/teams.py`
- **Expected Output**: Secure token generation via `secrets.token_urlsafe(32)` storing SHA-256 hash in DB.
