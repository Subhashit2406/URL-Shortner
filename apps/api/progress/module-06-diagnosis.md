# Module 06: Multi-Layer Bugs - Diagnosis & Architecture Review

## 1. Executive Summary
This document analyzes multi-layer architectural defects (Bug #9 and Bug #10) in LinkOps and details contract enforcement between components.

---

## 2. Bug #9: Stale Cache Serving Deleted Records

### Symptom
When an admin deletes a short link (`DELETE /links/:id`), the API responds with HTTP 200 OK. However, subsequent `GET /:shortCode` requests continue redirecting to the original target URL for up to 5 minutes (the cache TTL).

### Hypothesis & Root Cause
- **Hypothesis 1 (Disproven)**: Delete handler fails to remove DB record. (Verification showed PostgreSQL row was deleted).
- **Hypothesis 2 (Confirmed)**: Delete handler removes row from PostgreSQL but fails to invalidate Redis cache entry (`cache.del(key)`). Redirect path reads directly from Redis without checking PostgreSQL if cached.

### Architectural Fix
Add explicit cache invalidation in delete handler:
```typescript
await db.deleteLink(id);
await cache.del(`link:${shortCode}`);
```
*Note: Lowering TTL (e.g. 5m -> 30s) is an unacceptable band-aid fix because stale redirects still occur during the reduced window.*

---

## 3. Bug #10: Queue Retry Storm & Cascading Connection Exhaustion

### Symptom
Entire API hangs without returning errors or crashing. HTTP GET /health times out and service becomes completely unresponsive.

### 12-Step Chain of Causation
1. A background queue job fails (e.g., downstream network glitch or invalid payload).
2. Queue worker retries immediately without exponential backoff.
3. Queue worker acquires a database connection from shared connection pool.
4. Retry fails again due to same unhandled error.
5. Worker retries again immediately without max retry ceiling.
6. Steps 3-5 repeat in tight infinite loop.
7. Shared database connection pool reaches 100% utilization.
8. API endpoints requesting database connections block waiting for pool release.
9. API requests hang indefinitely waiting in connection queue.
10. Entire API becomes unresponsive.
11. `/health` endpoint times out due to inability to acquire DB connection.
12. Monitoring service flags API as DOWN.

### Root Cause & 3-Part Defense-in-Depth Fix
1. **Exponential Backoff**: Introduce delay multiplier (1s, 2s, 4s, 8s, 16s) to break tight retry loop.
2. **Dead-Letter Queue (DLQ)**: Cap maximum retries (e.g., 5 attempts) before moving unrecoverable job to DLQ.
3. **Bulkhead Connection Isolation**: Separate connection pools for API (e.g., 17 connections) and Queue Worker (e.g., 3 connections) so worker exhaustion cannot starve API endpoints.

---

## 4. Single Key Early Warning Alert
- **Metric**: `queue_job_retry_rate_per_minute` (or `queue_retry_count_5m`)
- **Threshold**: Fire warning alert if queue retry rate exceeds 10 retries/min over a 2-minute sliding window. This detects retry loops before connection pool saturation occurs.
