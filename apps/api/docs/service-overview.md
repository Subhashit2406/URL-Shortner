# UPSK Link Shortener / Notification Service Operations Manual

## 1. Purpose
The UPSK Link Shortener and Notification Service API processes URL alias creation, handles high-throughput link redirection, tracks click telemetry, and delivers notification webhooks. It enforces low-latency link lookup via Redis caching while storing persistent link mappings and audit logs in PostgreSQL.

---

## 2. Dependencies

| Dependency | Type | What Happens Without It | Fallback / Degradation Stance |
|---|---|---|---|
| PostgreSQL | Primary Datastore | Complete write failure; read cache miss fails | Fail-Closed: Mark `/ready` false, return HTTP 503 |
| Redis | In-Memory Cache | Cache misses increase DB load | Fail-Open: Fall through to DB, log warning |
| External Webhooks | HTTP Webhook Target | Webhook delivery delayed/retried | Circuit Breaker trips open, queues event in background |
| Local Filesystem | Log Storage | Storage exhaustion if unrotated | Log rotation configured (`maxBytes=10MB`) |
| DNS Resolver | Host Resolution | Cannot resolve DB/API hosts | Cache DNS lookups, fail-fast with structured error |

---

## 3. Endpoints

| Endpoint | Method | Purpose | Authentication |
|---|---|---|---|
| `/live` | GET | Liveness probe: returns `{"ok": true}` | Public |
| `/ready` | GET | Readiness probe: checks DB & Cache connections | Public |
| `/metrics` | GET | Prometheus metrics exporter (`http_requests_total`, latency) | Operational internal |
| `/api/v1/links` | POST | Create short URL alias | API Key Header |
| `/api/v1/links/{alias}` | GET | Fetch link metadata | Public |
| `/{alias}` | GET | Execute HTTP 302 redirect & log click telemetry | Public |
| `/_test/raise-500` | GET | Synthetic 500 exception endpoint for testing | Admin only |

---

## 4. Configuration Reference

All environment variables are validated at startup via Pydantic `BaseSettings` ([`app/config.py`](file:///c:/Users/subha/OneDrive/Desktop/CAW_assignment/apps/api/app/config.py)):

| Variable | Required | Runtime Safe? | Purpose | Default / Example |
|---|---|---|---|---|
| `APP_ENV` | Yes | Requires Restart | Deployment stage (`development`, `staging`, `production`) | `production` |
| `PORT` | Yes | Requires Restart | TCP listening port | `8000` |
| `DATABASE_URL` | Yes | Requires Restart | Async PostgreSQL connection string | `postgresql+asyncpg://appuser:secret@localhost:5432/upsk_db` |
| `JWT_SECRET` | Yes | Requires Restart | Secret key for JWT verification | `supersecret-key-32-chars-minimum!` |
| `ADMIN_API_KEY` | Yes | Requires Restart | Operational admin API key | `admin-secret-key-12345` |
| `CORS_ORIGIN` | No | Safe | Allowed CORS origins | `*` |
| `LOG_LEVEL` | No | Safe | Python logging verbosity (`INFO`, `DEBUG`, `WARNING`) | `INFO` |

Reference file: [`.env.example`](file:///c:/Users/subha/OneDrive/Desktop/CAW_assignment/apps/api/.env.example)

---

## 5. Deployment & Rollback Protocol

### Deploying a New Release
```bash
# 1. Trigger automated CI/CD pipeline push to main
git push origin main

# 2. Manual Container Deployment (Local/Staging test):
docker build -t notification-service:latest .
docker run -d --name notification-service-app -p 8000:8000 --env-file .env notification-service:latest

# 3. Verification Post-Deploy:
curl -f http://localhost:8000/live
# Expected: {"ok":true,"port":8000}

curl -f http://localhost:8000/ready
# Expected: {"ready":true,"database":"connected","port":8000}
```

### Rolling Back an Imperfect Release
```bash
# 1. Revert container image tag to previous SHA or release tag
docker stop notification-service-app
docker rm notification-service-app
docker run -d --name notification-service-app -p 8000:8000 --env-file .env notification-service:<previous-sha>

# 2. Verify Rollback Health:
curl -f http://localhost:8000/live
curl -f http://localhost:8000/ready
```

---

## 6. Ownership & Escalation Contacts

- **Team Owner**: Production Platform & Reliability Team (`#team-reliability`)
- **Primary On-Call**: Rotating Reliability Engineer (`@oncall-primary`)
- **Secondary On-Call**: Senior Platform Lead (`@oncall-secondary`)
- **Escalation Path**: Primary On-Call -> Secondary On-Call (10m) -> Engineering Manager (20m)
