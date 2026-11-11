import logging
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

from app.models import Link, ClickEvent
from app.schemas.analytics import LinkAnalyticsResponse, PurgeAnalyticsResponse

logger = logging.getLogger("upsk_api")


def hash_ip(ip_address: Optional[str]) -> Optional[str]:
    """Generates a SHA-256 hash of the client IP address for privacy compliance."""
    if not ip_address:
        return None
    return hashlib.sha256(ip_address.encode("utf-8")).hexdigest()


async def record_click_event_idempotent(
    session: AsyncSession,
    click_id: str,
    link_id: uuid.UUID,
    clicked_at: datetime,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    referrer: Optional[str] = None
) -> Optional[ClickEvent]:
    """Records a click event idempotently using click_id as unique constraint.
    
    If click_id has already been processed, it gracefully skips insertion
    to avoid double-counting click analytics.
    """
    # Check if click_id already recorded
    existing_stmt = select(ClickEvent).where(ClickEvent.click_id == click_id)
    existing_res = await session.execute(existing_stmt)
    existing_event = existing_res.scalar_one_or_none()
    if existing_event:
        logger.info(f"Idempotent skip: click_id '{click_id}' already recorded.")
        return existing_event

    ip_hashed = hash_ip(ip_address)
    click_event = ClickEvent(
        click_id=click_id,
        link_id=link_id,
        clicked_at=clicked_at,
        ip_hash=ip_hashed,
        user_agent=user_agent[:500] if user_agent else None,
        referrer=referrer[:500] if referrer else None
    )

    try:
        session.add(click_event)
        await session.commit()
        await session.refresh(click_event)
        logger.info(f"Recorded click_event '{click_id}' for link_id '{link_id}'")
        return click_event
    except IntegrityError:
        await session.rollback()
        logger.info(f"IntegrityError handled: click_id '{click_id}' duplicate concurrent insertion skipped.")
        return None


async def get_link_analytics(
    session: AsyncSession,
    link_id: uuid.UUID,
    from_time: Optional[datetime] = None,
    to_time: Optional[datetime] = None
) -> LinkAnalyticsResponse:
    """Retrieves aggregated click count and last clicked timestamp for a short link."""
    # Verify link exists
    link_stmt = select(Link).where(Link.id == link_id)
    link_res = await session.execute(link_stmt)
    link = link_res.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # Set default time bounds
    window_from = from_time or datetime(2000, 1, 1, tzinfo=timezone.utc)
    window_to = to_time or datetime(2100, 1, 1, tzinfo=timezone.utc)

    # Aggregate total clicks & last clicked timestamp
    agg_stmt = (
        select(
            func.count(ClickEvent.id).label("total_clicks"),
            func.max(ClickEvent.clicked_at).label("last_clicked_at")
        )
        .where(
            ClickEvent.link_id == link_id,
            ClickEvent.clicked_at >= window_from,
            ClickEvent.clicked_at <= window_to
        )
    )
    agg_res = await session.execute(agg_stmt)
    row = agg_res.one()

    return LinkAnalyticsResponse(
        link_id=link.id,
        code=link.code,
        total_clicks=row.total_clicks or 0,
        last_clicked_at=row.last_clicked_at,
        window_from=window_from,
        window_to=window_to
    )


async def purge_old_clicks(
    session: AsyncSession,
    retention_days: int = 30
) -> PurgeAnalyticsResponse:
    """Purges historical click events older than the specified retention cutoff."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)

    purge_stmt = delete(ClickEvent).where(ClickEvent.clicked_at < cutoff)
    res = await session.execute(purge_stmt)
    await session.commit()

    purged_count = res.rowcount or 0
    logger.info(f"Purged {purged_count} click events older than {retention_days} days (cutoff: {cutoff.isoformat()})")

    return PurgeAnalyticsResponse(
        retention_days=retention_days,
        purged_count=purged_count,
        cutoff_timestamp=cutoff
    )
