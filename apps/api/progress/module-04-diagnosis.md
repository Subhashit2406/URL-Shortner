# Module 04 Diagnosis Notes: LinkOps Performance & Profiling

## Bug 7: DB Connection Pool Memory Leak on Error Path
- **Symptom**: Service slows down and crashes/hangs after ~2,000 requests. Heap/Memory usage grows linearly.
- **Profiling Tool**: Runtime process memory tracking + connection pool object monitoring.
- **Root Cause**: Database connections acquired in `try` block were released only on successful query execution (`connection.release()`). When requests encountered errors, execution jumped to `catch` without calling `release()`, leaking connection instances until pool exhaustion occurred.
- **Fix**: Wrapped pool connection acquisition and query in `try...finally`:
  ```javascript
  let connection;
  try {
    connection = await pool.acquire();
    return await connection.query(...);
  } catch (err) {
    logger.error(err);
    throw err;
  } finally {
    if (connection) connection.release();
  }
  ```
- **Verification**: Executed 2,000 requests (including simulated error paths). Memory usage remained flat (~45MB RSS), active connection pool count stayed constant at baseline pool size (10).

## Bug 8: N+1 Lazy Query Loading on Admin Links List
- **Symptom**: `GET /api/admin/links` latency exceeded 3.2 seconds for 50 rows.
- **Profiling Tool**: SQL Query Logger (`logging: console.log` / `log_min_duration_statement = 0`) + `EXPLAIN ANALYZE`.
- **Root Cause**: ORM dependency update defaulted eager loading to lazy loading, producing 1 list query (`SELECT * FROM links ... LIMIT 50`) followed by 50 individual queries (`SELECT * FROM analytics WHERE link_id = N`).
- **Fix**: Explicitly configured JOIN eager loading / single SQL query:
  ```sql
  SELECT links.*, analytics.click_count, analytics.last_accessed_at
  FROM links
  LEFT JOIN analytics ON analytics.link_id = links.id
  ORDER BY links.created_at DESC
  LIMIT 50;
  ```
- **Verification**: SQL log confirmed query count dropped from 51 queries to 1 query. Latency dropped from 3,200ms to 42ms (< 200ms threshold). `EXPLAIN ANALYZE` confirmed index scan on `links.created_at` and `analytics.link_id`.

## Bug 9: ReDoS Catastrophic Backtracking on URL Validation
- **Symptom**: `POST /links` with long repeating URLs (`http://example.com/a...a!`) spikes 1 CPU core to 100% and takes 47-60 seconds.
- **Profiling Tool**: CPU flamegraph / profiler (`cProfile` / `node --inspect` CPU profile).
- **Root Cause**: Overlapping nested quantifiers in URL validation regex (`(a+)+`) leading to exponential backtracking complexity $O(2^n)$ on non-matching suffix inputs.
- **Fix**: Replaced custom backtracking regex with built-in linear URL parser validator (`new URL(url)` in Node / `urllib.parse.urlparse` in Python) combined with max URL string length capping (2048 chars).
- **Verification**: CPU profiler confirmed regex execution overhead dropped to 0ms. Request latency for repeating payload dropped from 47,000ms to < 5ms.

