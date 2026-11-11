# OrderFlow Service — Onboarding & Local Development Guide

OrderFlow is a core REST API service for order creation, payment settlement, status tracking, and asynchronous refund processing in the platform e-commerce stack.

---

## Service Overview & Key Ports

| Component | Technology | Default Local Port | Environment Variable | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **API Application** | Python 3.11 / FastAPI | `8080` | `PORT=8080` | Core HTTP REST service |
| **Primary Database** | PostgreSQL 15 | `5432` | `DATABASE_URL` | Persistent order & transaction storage |
| **Cache & Queue** | Redis 7 | `6379` | `REDIS_URL`, `CELERY_BROKER_URL` | Rate limiting & Celery job queue |
| **Background Worker** | Celery 5.3 | N/A | `CELERY_BROKER_URL` | Asynchronous refund processing |

---

## 1. Local Prerequisites Check
Before starting, verify that Docker Desktop and Python 3.11 are installed on your machine.

Run these exact commands in your terminal:

```bash
docker --version || echo "Docker missing! Install from https://docs.docker.com/get-docker/"
python3 --version || echo "Python 3 missing! Install Python 3.11+"
git --version || echo "Git missing!"
```

---

## 2. Environment Setup

### Step 2.1: Clone Repository
```bash
git clone https://github.com/company/orderflow.git
cd orderflow
```

### Step 2.2: Create Local Environment File
Copy the example configuration to `.env`:

```bash
cat << 'EOF' > .env
PORT=8080
DATABASE_URL=postgresql://user:pass@localhost:5432/orderflow
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
AUTH_SERVICE_URL=https://auth.internal.company.com
STRIPE_API_KEY=sk_test_mock_key_12345
SENTRY_DSN=https://mock_sentry@sentry.io/123456
LOG_LEVEL=DEBUG
EOF
```

---

## 3. Starting Dependency Services (Database & Redis)

Start PostgreSQL 15 and Redis 7 in Docker containers:

```bash
docker run -d --name orderflow-postgres -e POSTGRES_USER=user -e POSTGRES_PASSWORD=pass -e POSTGRES_DB=orderflow -p 5432:5432 postgres:15
docker run -d --name orderflow-redis -p 6379:6379 redis:7
```

Verify containers are running:
```bash
docker ps --filter "name=orderflow"
```

---

## 4. Database Migrations & Virtual Environment

### Step 4.1: Create Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate || venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4.2: Run Database Migrations
```bash
alembic upgrade head
```

---

## 5. Running the Application & Background Worker

### Terminal 1: Start FastAPI REST API Server
```bash
source venv/bin/activate || venv\Scripts\activate
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### Terminal 2: Start Celery Asynchronous Worker
```bash
source venv/bin/activate || venv\Scripts\activate
celery -A orderflow.worker worker --loglevel=info
```

---

## 6. Running Test Suite & Health Probe

### Step 6.1: Execute Automated Unit & Integration Tests
```bash
pytest tests/ -v
```

### Step 6.2: Verify Health Probe Endpoint
```bash
curl -i http://localhost:8080/health
```
*Expected Output:* `HTTP/1.1 200 OK` with JSON `{"status": "healthy", "database": "connected", "redis": "connected"}`.

---

## 7. Escalation & Team Contacts

- **Primary Slack Channel:** `#orderflow-oncall`
- **Database Team:** `#data-eng`
- **Infrastructure & Kubernetes:** `#platform-infra`
- **PagerDuty Escalation:** Policy `OrderFlow Primary`
