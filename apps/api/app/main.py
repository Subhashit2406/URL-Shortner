from contextlib import asynccontextmanager
import json
import logging
import time
import uuid

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

from app.config import settings
from app.database import engine, Base
from app.routers.links import router as links_router
from app.routers.redirect import router as router_redirect

# Structured JSON Formatting for logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_obj = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname.lower(),
            "message": record.getMessage(),
            "service_name": "notification-service",
            "request_id": getattr(record, "request_id", "system"),
        }
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_obj.update(record.extra)
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("upsk_api")
logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
logger.handlers = [handler]

# Prometheus Metrics Definition
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP Requests",
    ["method", "path", "status"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path"]
)

ACTIVE_CONNECTIONS = Gauge(
    "active_connections",
    "Active connections gauge"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure database schema tables exist
    logger.info(
        f"Service starting in environment={settings.app_env.value} on port={settings.port}"
    )
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as exc:
        logger.warning(f"Database initialization skipped or offline: {exc}")

    yield

    # Shutdown: Dispose engine connections cleanly
    try:
        await engine.dispose()
    except Exception:
        pass


app = FastAPI(
    title="UPSK Link Shortener API",
    version="1.0.0",
    lifespan=lifespan
)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    ACTIVE_CONNECTIONS.inc()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:
        latency = time.perf_counter() - start_time
        HTTP_REQUESTS_TOTAL.labels(method=request.method, path=request.url.path, status=str(status_code)).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(method=request.method, path=request.url.path).observe(latency)
        logger.exception("Unhandled request exception", extra={"request_id": request_id, "path": request.url.path})
        response = JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": {"code": "INTERNAL_SERVER_ERROR", "message": "An unexpected server error occurred", "request_id": request_id}},
        )
    finally:
        ACTIVE_CONNECTIONS.dec()

    latency = time.perf_counter() - start_time
    HTTP_REQUESTS_TOTAL.labels(method=request.method, path=request.url.path, status=str(status_code)).inc()
    HTTP_REQUEST_DURATION_SECONDS.labels(method=request.method, path=request.url.path).observe(latency)

    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    code_map = {
        400: "BAD_REQUEST", 401: "UNAUTHORIZED", 403: "FORBIDDEN",
        404: "NOT_FOUND", 409: "CONFLICT", 422: "UNPROCESSABLE_ENTITY"
    }
    error_code = code_map.get(exc.status_code, f"HTTP_{exc.status_code}")
    response = JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": error_code, "message": str(exc.detail), "request_id": request_id}},
        headers=exc.headers,
    )
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    response = JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"error": {"code": "VALIDATION_ERROR", "message": "Request validation failed", "request_id": request_id}},
    )
    response.headers["X-Request-ID"] = request_id
    return response


# Include API Routers
app.include_router(links_router)
app.include_router(router_redirect)


@app.get("/live")
@app.get("/health")
def health():
    return {"ok": True, "port": settings.port}


@app.get("/ready")
async def readiness():
    db_ok = True
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    status_code = status.HTTP_200_OK if db_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={"ready": db_ok, "database": "connected" if db_ok else "disconnected", "port": settings.port}
    )


@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/_test/raise-500", include_in_schema=False)
def test_500_route():
    raise RuntimeError("Simulated unexpected server error for Module 04/05 verification")