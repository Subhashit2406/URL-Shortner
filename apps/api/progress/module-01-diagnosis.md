# Module 01 Diagnosis Notes: LinkOps URL Shortener

## Bug 1: Service Will Not Start (Database Connection Error)
- **Symptom**: LinkOps API crashes on startup with database connection error.
- **Hypothesis A**: Database container is down or unhealthy.
  - **Command**: `docker compose ps` / `docker ps`
  - **Observation**: DB container is healthy and listening on 5432. Hypothesis A disproven.
- **Hypothesis B**: Configuration contract mismatch (`DB_URL` vs `DATABASE_URL`).
  - **Command**: `grep -E "DB_URL|DATABASE_URL" app/config.py .env`
  - **Observation**: `.env` specifies `DB_URL` while `config.py` expects `DATABASE_URL`. Hypothesis B confirmed.
- **Fix**: Synchronized `.env` configuration to export `DATABASE_URL`.
- **Verification proof**: `curl -sS http://localhost:3000/health` returns `{"ok": true}`.

## Bug 2: Pagination Overlap Across Pages
- **Symptom**: Duplicate items appear on page boundary (last item on page 1 is first item on page 2).
- **Hypothesis A**: Off-by-one error in SQL `OFFSET` calculation `offset = page * limit` instead of `(page - 1) * limit`.
  - **Command**: `curl -sS "http://localhost:3000/api/admin/links?page=1&limit=10"` vs `page=2`
  - **Observation**: Page 2 begins at offset 10 instead of 10, but offset calculation was `(page - 1) * limit + 1` causing 1-record overlap. Hypothesis A confirmed.
- **Hypothesis B**: Unstable sort order without tie-breaking primary key.
  - **Command**: Repeated SQL queries with explicit `ORDER BY created_at DESC, id DESC`
  - **Observation**: Sort order is deterministic once offset calculation is corrected.
- **Fix**: Updated pagination offset formula to `offset = (page - 1) * limit`.
- **Verification proof**: `curl` across pages 1, 2, and 3 verifies 0 duplicate IDs across page boundaries.
