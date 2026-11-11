import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, AsyncSessionLocal
from app.services import links_service
from app.services.analytics_service import record_click_event_idempotent
from app.services.cache_service import (
    check_redirect_rate_limit,
    get_redirect_cache,
    set_redirect_cache,
)

logger = logging.getLogger("upsk_api")

router = APIRouter(prefix="/r", tags=["Redirect"])


async def async_record_click_task(
    click_id: str,
    link_id: uuid.UUID,
    clicked_at: datetime,
    client_ip: str,
    user_agent: str | None,
    referrer: str | None
):
    """Background task processing click event analytics idempotently in a separate DB session."""
    try:
        async with AsyncSessionLocal() as session:
            await record_click_event_idempotent(
                session=session,
                click_id=click_id,
                link_id=link_id,
                clicked_at=clicked_at,
                ip_address=client_ip,
                user_agent=user_agent,
                referrer=referrer
            )
    except Exception as exc:
        logger.warning(f"Background click event logging failed open for click_id '{click_id}': {exc}")


@router.get("/{code}", status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_short_code_endpoint(
    code: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Public short URL redirect with Redis caching, IP rate-limiting, and async background click analytics."""
    # 1. Extract request details & IP
    client_ip = request.client.host if request.client else "127.0.0.1"
    user_agent = request.headers.get("user-agent")
    referrer = request.headers.get("referer")

    # 2. Enforce IP-based rate limiting (abuse spike protection)
    is_allowed = await check_redirect_rate_limit(client_ip)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many redirect requests. Please try again later.",
            headers={"Retry-After": "60"}
        )

    # 3. Try Redis Cache-Aside Hit Path
    cached_long_url = await get_redirect_cache(code)
    if cached_long_url:
        logger.info(f"Cache HIT for short code '{code}' -> '{cached_long_url}'")
        link = await links_service.get_link_by_code(db, code)
        if link:
            click_id = str(uuid.uuid4())
            background_tasks.add_task(
                async_record_click_task,
                click_id=click_id,
                link_id=link.id,
                clicked_at=datetime.now(timezone.utc),
                client_ip=client_ip,
                user_agent=user_agent,
                referrer=referrer
            )
        return RedirectResponse(url=cached_long_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    # 4. Cache Miss or Redis Offline Fallback Path -> Read from PostgreSQL DB
    logger.info(f"Cache MISS for short code '{code}' -> querying PostgreSQL")
    link = await links_service.get_link_by_code(db, code)

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Short code not found or expired"
        )

    # Schedule async background click recording task
    click_id = str(uuid.uuid4())
    background_tasks.add_task(
        async_record_click_task,
        click_id=click_id,
        link_id=link.id,
        clicked_at=datetime.now(timezone.utc),
        client_ip=client_ip,
        user_agent=user_agent,
        referrer=referrer
    )

    # 5. Populate Redis Cache on Miss
    await set_redirect_cache(code, link.long_url)

    # 6. Return HTTP 307 Temporary Redirect
    return RedirectResponse(url=link.long_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
