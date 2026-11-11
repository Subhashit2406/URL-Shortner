# Module 03 Diagnosis & Reproduction Notes: LinkOps Concurrency

## Bug 5: Check-Then-Act Race Condition on Analytics Bucket Insertion
- **Symptom**: Intermittent 500 error on GET `/:shortCode` under high traffic: `duplicate key value violates unique constraint "analytics_link_id_bucket_unique"`.
- **Hypothesis**: Concurrency check-then-act race condition. Multiple concurrent HTTP requests for the same short code check for an existing analytics bucket simultaneously, both observe `SELECT ... -> null`, and both execute `INSERT INTO analytics`, triggering unique constraint violation on the second write.
- **Reproduction Script** (`scripts/repro_race.py`):
  ```python
  import asyncio, aiohttp
  async def main():
      async with aiohttp.ClientSession() as session:
          tasks = [session.get("http://localhost:3000/test-link", allow_redirects=False) for _ in range(10)]
          results = await asyncio.gather(*tasks, return_exceptions=True)
          errors = [r for r in results if getattr(r, 'status', None) == 500]
          print(f"Errors: {len(errors)}")
  asyncio.run(main())
  ```
- **Observation**: Reproduced 500 error on 10 concurrent requests.
- **Fix**: Replaced separate `SELECT` and `INSERT` steps with atomic PostgreSQL `UPSERT`:
  ```sql
  INSERT INTO analytics (link_id, timestamp_bucket, count)
  VALUES ($1, $2, 1)
  ON CONFLICT (link_id, timestamp_bucket)
  DO UPDATE SET count = analytics.count + 1;
  ```
- **Verification proof**: Executed reproduction script 10 consecutive times under 10-concurrency load -> 0 HTTP 500 errors, exact analytics count = 100.

## Bug 6: Out-of-Order Timestamp Overwrite in Analytics Upsert
- **Symptom**: `last_accessed_at` on analytics row shows earlier timestamp instead of the most recent request under concurrent load.
- **Cause**: Out-of-order execution during concurrent UPSERTs overwriting `last_accessed_at = EXCLUDED.last_accessed_at` with stale values from delayed requests.
- **Fix**: Use PostgreSQL `GREATEST(analytics.last_accessed_at, EXCLUDED.last_accessed_at)` or DB `NOW()` in `DO UPDATE SET` clause to guarantee monotonic forward progression of `last_accessed_at`.
  ```sql
  ON CONFLICT (link_id, timestamp_bucket)
  DO UPDATE SET
    count = analytics.count + 1,
    last_accessed_at = GREATEST(analytics.last_accessed_at, EXCLUDED.last_accessed_at);
  ```

