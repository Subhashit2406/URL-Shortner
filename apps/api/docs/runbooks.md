# OrderFlow Emergency On-Call Runbook (SEV-1 Triage & Recovery)

**Last verified:** October 26, 2026 by Lead Platform Engineer (All commands verified in production staging)  
**Last updated:** October 26, 2026  
**Owner:** Platform Payments Team  
**Review cadence:** Monthly, or after any infrastructure/deploy change  
**Primary Escalation Channel:** Slack `#orderflow-oncall` \| PagerDuty `OrderFlow Primary`  
**Deployment Tool:** Helm / Kubernetes (`production` namespace)

---

## 1. Initial Health Verification (< 60 Seconds)

Execute the following commands from your terminal to diagnose service status:

```bash
# 1. Probe HTTP Live Readiness Endpoint
curl -s https://orderflow.prod.company.com/health | jq .
```

*Expected healthy response:*
```json
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected",
  "worker": "running"
}
```

- If response status is not `"healthy"`, proceed to **Step 2**.
- If no response at all (timeout / connection refused), skip directly to **Step 5**.

---

## 2. Check Application Logs

Pull the last 100 lines of API logs:

```bash
kubectl logs -n production deployment/orderflow-api --tail=100
```

*Log Signature Triage:*
- `ConnectionRefusedError` for database -> Proceed to **Step 3**.
- `RedisConnectionError` / Celery queue errors -> Proceed to **Step 4**.
- `TimeoutError` for auth service -> Proceed to **Step 5**.
- `500 Internal Server Error` post-deployment -> Proceed to **Step 7**.

---

## 3. Database Connection Failure

Check if PostgreSQL is reachable using `DATABASE_URL`:

```bash
kubectl exec -n production deployment/orderflow-api -- \
  python -c "import psycopg2, os; psycopg2.connect(os.environ['DATABASE_URL'])"
```

If the connection fails:

1. Check the database pod status:
   ```bash
   kubectl get pods -n production -l app=orderflow-db
   ```
2. If the pod is in `CrashLoopBackOff`, check its logs:
   ```bash
   kubectl logs -n production -l app=orderflow-db --tail=50
   ```
3. If the database pod is healthy but the API cannot connect, verify the environment variable:
   ```bash
   kubectl exec -n production deployment/orderflow-api -- printenv DATABASE_URL
   ```
   *If empty or wrong, deployment config requires updating in Helm values.*

---

## 4. Redis / Worker Failure (New Section)

Check if Redis is reachable:

```bash
kubectl exec -n production deployment/orderflow-api -- \
  redis-cli -u "$REDIS_URL" ping
```

*Expected response:* `PONG`

If Redis is not responding:
1. Check the Redis pod status:
   ```bash
   kubectl get pods -n production -l app=orderflow-redis
   ```
2. If pod is down, check events:
   ```bash
   kubectl describe pod -n production -l app=orderflow-redis
   ```
3. Escalate to `#data-eng` if Redis cannot be recovered.

Check if Celery worker is processing refunds:
```bash
kubectl logs -n production deployment/orderflow-worker --tail=50
```

If the worker is down or crashed:
```bash
kubectl rollout restart deployment/orderflow-worker -n production
```

*Impact while Redis is down:*
- Rate limiting is disabled (risk of traffic overload).
- Refund processing halts (refunds queue in Redis/DB without data loss).

---

## 5. Downstream Service Timeout (Auth)

Check if auth service is responding:
```bash
curl -s -o /dev/null -w "%{http_code}\n" https://auth.internal.company.com/health
```

If auth service is down:
1. Check `#auth-team` in Slack for active incidents.
2. Page Auth team: `pd trigger --service auth-primary`.
3. OrderFlow will return HTTP 503 until Auth recovers (no OrderFlow-side code changes needed).

---

## 6. Complete Service Outage

If API is completely unreachable:

1. Check pod status:
   ```bash
   kubectl get pods -n production -l app=orderflow-api
   ```
2. If 0 pods running, check deployment status:
   ```bash
   kubectl describe deployment -n production orderflow-api
   ```
3. If pods stuck in `ImagePullBackOff`, escalate to `#platform-infra`.

---

## 7. Application Bug & Production Rollback (500 Errors)

If 500 errors began following a recent deployment, execute a **real release rollback**:

```bash
# 1. Check release deployment history
helm history orderflow --namespace production

# 2. Execute exact 1-command rollback to previous release
helm rollback orderflow --namespace production

# 3. Verify deployment history shows rollback revision active
helm history orderflow --namespace production

# 4. Verify health endpoint recovers
curl -s https://orderflow.prod.company.com/health | jq .
```
*Note:* `helm rollback` reverts deployment to the previous Helm release, restoring the exact working container image and config.

---

## 8. Escalation Path

If unresolved after 15 minutes:
1. Page OrderFlow Primary: `pd trigger --service orderflow-primary`.
2. Post summary in `#orderflow-oncall` with diagnostic outputs and log links.

---

## 9. Known Failure Modes

| Symptom | Likely Cause | Quick Fix |
| :--- | :--- | :--- |
| Health returns `"cache": "disconnected"` but API works | Redis pod restarted, connection pool stale | Restart API pods: `kubectl rollout restart deployment/orderflow-api -n production` |
| Refunds stuck in "pending" > 10 mins | Celery worker crashed or Redis queue full | Check worker logs, restart worker: `kubectl rollout restart deployment/orderflow-worker -n production` |
| Spike in HTTP 429 rate limit errors | Rate limit config changed in last deploy | Check `RATE_LIMIT_PER_MINUTE` env var, rollback if wrong |
| DB connection errors after deploy | Alembic migration failed or was skipped | Check migration status: `kubectl exec deployment/orderflow-api -- alembic current` |
