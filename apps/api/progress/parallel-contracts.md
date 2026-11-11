# Parallel Agent Management — Interface Contracts

## Overview & Architecture Integration
This document specifies the explicit interface contracts for three parallel agents developing independent features in the Team Collaboration domain (Comment Threads, @Mention Parsing/Notification, Audit Logging) using the **Interface-First** coordination pattern.

---

## Agent 1: Comment Threads
- **Scope**: Threaded task comments REST endpoints & data persistence.
- **Creates**:
  - `src/comments/router.py`
  - `src/comments/schemas.py`
  - `src/comments/models.py`
  - `tests/test_comments.py`
- **Reads (ReadOnly)**:
  - `src/teams/models.py`
  - `src/auth/deps.py`
- **Modifies**:
  - `src/main.py` (mount router `/teams/{team_id}/tasks/{task_id}/comments`)
- **Data Shape**:
  ```json
  {
    "id": "uuid-v4",
    "task_id": "uuid-v4",
    "author_id": "uuid-v4",
    "body": "string (1-5000 chars)",
    "parent_id": "uuid-v4 | null",
    "created_at": "ISO-8601"
  }
  ```
- **Events Emitted**: `comment.created` -> `{comment_id, task_id, author_id, body}`

---

## Agent 2: @Mention Parsing & Notification
- **Scope**: Extract @mentions from text and dispatch user notifications.
- **Creates**:
  - `src/notifications/mention_parser.py`
  - `src/notifications/service.py`
  - `tests/test_mentions.py`
- **Reads (ReadOnly)**:
  - `src/teams/models.py`
- **Modifies**: None (Pure functional utility and standalone service)
- **Data Shape**:
  ```json
  {
    "raw_handle": "@john_doe",
    "username": "john_doe",
    "user_id": "uuid-v4 | null"
  }
  ```
- **Integration Contract**: `parse_mentions(text: str) -> list[MentionResult]`

---

## Agent 3: Audit Log & Security Events
- **Scope**: Immutable audit event logging and retrieval middleware.
- **Creates**:
  - `src/audit/middleware.py`
  - `src/audit/models.py`
  - `src/audit/router.py`
  - `tests/test_audit.py`
- **Reads (ReadOnly)**:
  - `src/auth/deps.py`
- **Modifies**:
  - `src/main.py` (register AuditMiddleware and mount `/audit-logs`)
- **Data Shape**:
  ```json
  {
    "id": "uuid-v4",
    "action": "CREATE | UPDATE | DELETE",
    "resource_type": "team | task | comment",
    "resource_id": "uuid-v4",
    "actor_id": "uuid-v4",
    "timestamp": "ISO-8601"
  }
  ```

---

## SYSTEM-LEVEL INTEGRATION CONTRACT (Added via FIX Step)
1. **Event Bus Subscription**:
   - All resource-mutating operations (`comment.created`, `comment.updated`, `comment.deleted`) MUST publish events onto the shared event bus with payload format `{resource_type}.{action}`.
2. **Audit Subscriber Bridge**:
   - An explicit event subscriber `src/audit/subscriber.py` listens to `{resource_type}.*` events and dispatches calls to `audit_logger.record(...)`.
   - Disambiguates nested routes (e.g. `/tasks/{id}/comments`) from parent resource updates (`task`).
3. **Resource Type Registry**:
   - Registered resource enums: `team`, `task`, `comment`, `invitation`, `user`.
