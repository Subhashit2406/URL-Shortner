# Team Collaboration Feature — Task Tree & Decomposition

## Strategy & Granularity
- **Decomposition Approach**: Top-Down (mapped cross-cutting concerns upfront)
- **Task Granularity**: Medium-Grained (8 Atomic Tasks, <150 lines per diff)

---

## Task Tree Overview (8 Tasks)

```
[Task 1: Team & Member Schema] ──┬──> [Task 2: Team CRUD Endpoints] ───> [Task 4: Role-Based RBAC Middleware] ──┬──> [Task 6: Audit Log Recording]
                                └──> [Task 3: Invite Model & Endpoints] ─> [Task 5: Invite Accept & Replay Block] ┘
                                                                       └──> [Task 7: Activity Feed Service] ──────> [Task 8: Integration Test Suite]
```

---

## Detailed Task Specifications

### Task 1: Team & Member Data Models
- **Input Context**: `app/models.py`, `app/database.py`
- **Expected Output**: SQLAlchemy ORM models `Team` (id, name, owner_id, created_at) and `TeamMember` (id, team_id, user_id, role, joined_at).
- **Acceptance Criteria**: Database tables `teams` and `team_members` created with foreign key constraints.
- **Dependencies**: None (Root)

### Task 2: Team CRUD Endpoints
- **Input Context**: `app/models.py`, `app/routers/links.py`
- **Expected Output**: Router `app/routers/teams.py` with `POST /teams` and `GET /teams/{id}`.
- **Acceptance Criteria**: `POST /teams` returns HTTP 201 with team payload; `GET /teams/{id}` returns HTTP 200/404.
- **Dependencies**: Task 1

### Task 3: Invitation Model & Endpoints
- **Input Context**: `app/models.py`, `app/routers/teams.py`
- **Expected Output**: Model `TeamInvite` (id, team_id, email, token_hash, expires_at, status) and `POST /teams/{id}/invites`.
- **Acceptance Criteria**: `POST /teams/{id}/invites` generates 32-byte secure token and returns HTTP 201.
- **Dependencies**: Task 1

### Task 4: Role-Based Access Control (RBAC) Dependency
- **Input Context**: `app/models.py`, `app/routers/teams.py`
- **Expected Output**: FastAPI dependency `require_team_role(min_role)` verifying user role in `TeamMember`.
- **Acceptance Criteria**: Returns HTTP 403 Forbidden when non-admin attempts admin actions.
- **Dependencies**: Task 2

### Task 5: Invite Acceptance & Anti-Replay Engine
- **Input Context**: `app/models.py`, `app/routers/teams.py`
- **Expected Output**: Endpoint `POST /invites/accept` marked token as `accepted` atomically.
- **Acceptance Criteria**: Re-submitting an accepted token returns HTTP 400 Bad Request (anti-replay).
- **Dependencies**: Task 3

### Task 6: Audit Log Recording
- **Input Context**: `app/models.py`, `app/routers/teams.py`
- **Expected Output**: ORM model `AuditLog` and async audit logger `log_team_action(team_id, actor_id, action)`.
- **Acceptance Criteria**: Action `team.member_added` creates immutable audit entry with timestamp.
- **Dependencies**: Task 4, Task 5

### Task 7: Activity Feed Service
- **Input Context**: `app/models.py`, `app/routers/teams.py`
- **Expected Output**: Router `app/routers/activity.py` returning ordered event feed `GET /teams/{id}/activity`.
- **Acceptance Criteria**: Activity items sorted chronologically descending with pagination `page_size <= 50`.
- **Dependencies**: Task 5

### Task 8: Integration & Security Test Suite
- **Input Context**: `tests/`, `scripts/module-09-verify-testing.py`
- **Expected Output**: Test suite `scripts/module-11-verify-collaboration.py` verifying full flow.
- **Acceptance Criteria**: 100% test pass covering CRUD, RBAC 403, and token replay prevention.
- **Dependencies**: Task 6, Task 7

---

## Full Prompt Text for First 3 Tasks

### Prompt 1 (Task 1: Team & Member Data Models)
```text
Create the SQLAlchemy ORM models for Team and TeamMember in `app/models.py`.
The Team model must include: id (UUID primary key), name (String 100, required), owner_id (String 60, required), created_at (DateTime UTC).
The TeamMember model must include: id (UUID primary key), team_id (FK to teams.id), user_id (String 60), role (Enum: 'admin', 'member', 'viewer'), joined_at (DateTime UTC).
Follow existing SQLAlchemy 2.0 declarative patterns in `app/models.py`. Do not install new dependencies.
```

### Prompt 2 (Task 2: Team CRUD Endpoints)
```text
Create `app/routers/teams.py` and register it in `app/main.py`.
Implement:
1. `POST /teams`: accepts Pydantic schema `TeamCreate` (name), validates non-empty string, creates Team record, and assigns creator as 'admin' in TeamMember. Returns HTTP 201.
2. `GET /teams/{id}`: returns team details and member count. Returns HTTP 200 or 404.
Use existing APIRouter conventions from `app/routers/links.py` and error envelope patterns.
```

### Prompt 3 (Task 3: Invitation Model & Endpoints)
```text
Add TeamInvite model to `app/models.py` (id, team_id, email, token_hash, expires_at, status='pending').
Add endpoint `POST /teams/{id}/invites` in `app/routers/teams.py` accepting `email`.
Generate a cryptographically secure 32-byte token using `secrets.token_urlsafe(32)`, store its SHA-256 hash in `token_hash`, set `expires_at` to 7 days in the future, and return HTTP 201 with the raw invite token.
```

---

## Critical Path & Riskiest Task
- **Critical Path**: `Task 1` -> `Task 3` -> `Task 5` -> `Task 7` -> `Task 8` (4 sequential dependency steps).
- **Riskiest Task**: **Task 5 (Invite Acceptance & Anti-Replay Engine)** due to race conditions during concurrent token consumption and replay attack vectors.

---

## Interface Contracts (FIX Step Resolution)

### Contract 1: Task 1 (Models) -> Task 2 (Team CRUD)
- **Task 1 Produces**:
  - `Team` model & `teams` table: `id` (UUID), `name` (String), `owner_id` (String), `created_at` (DateTime).
  - `TeamMember` model & `team_members` table: `id` (UUID), `team_id` (FK to teams.id), `user_id` (String), `role` (Enum: admin, member, viewer).
- **Task 2 Expects**:
  - `Team` model importable from `app.models`.
  - Creator assigned `role='admin'` in `team_members` upon team creation.
- **Shared Agreement**: Single transaction creates `teams` record and inserts owner `team_members` row.

### Contract 2: Task 3 (Invite Endpoint) -> Task 5 (Invite Acceptance)
- **Task 3 Produces**: `TeamInvite` record with `token_hash` (SHA-256 string) and `status='pending'`.
- **Task 5 Expects**: SHA-256 hash of incoming raw token matches `TeamInvite.token_hash` where `status='pending'` and `expires_at > now()`.
- **Shared Agreement**: Atomic state transition from `pending` to `accepted`. Re-used tokens return HTTP 400 Bad Request.

