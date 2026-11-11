import uuid
import secrets
import hashlib
from datetime import datetime, timezone
from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Link, ClickEvent
from app.schemas.link import LinkCreate, LinkResponse, LinkListResponse, LinkUpdate
from app.schemas.search import SortByEnum, SortOrderEnum


def generate_short_code(length: int = 6) -> str:
    """Generate a collision-resistant URL-safe base64 short code."""
    return secrets.token_urlsafe(length)[:length].replace("-", "x").replace("_", "y")


def hash_ip(ip_address: str | None) -> str | None:
    """Compute SHA-256 hash of IP address for GDPR compliance."""
    if not ip_address:
        return None
    return hashlib.sha256(ip_address.encode("utf-8")).hexdigest()


async def create_link(
    session: AsyncSession,
    payload: LinkCreate,
    created_by: str = "anonymous",
    base_url: str = "http://localhost:8000"
) -> LinkResponse:
    """Create a new short link with unique short_code generation."""
    # Attempt code generation with collision retry loop
    for _ in range(5):
        code = generate_short_code(6)
        stmt = select(Link).where(Link.code == code)
        res = await session.execute(stmt)
        if res.scalar_one_or_none() is None:
            break
    else:
        # Fallback to 8-char code if 6-char collision occurs
        code = generate_short_code(8)

    new_link = Link(
        code=code,
        long_url=payload.long_url,
        created_by=created_by,
    )
    session.add(new_link)
    await session.commit()
    await session.refresh(new_link)

    short_url = f"{base_url}/r/{new_link.code}"
    return LinkResponse(
        id=new_link.id,
        code=new_link.code,
        short_url=short_url,
        long_url=new_link.long_url,
        created_by=new_link.created_by,
        created_at=new_link.created_at,
        expires_at=payload.expires_at,
        tags=payload.tags
    )


async def get_link_by_id(
    session: AsyncSession,
    link_id: uuid.UUID,
    base_url: str = "http://localhost:8000"
) -> LinkResponse | None:
    """Retrieve a single link record by primary key UUID."""
    stmt = select(Link).where(Link.id == link_id)
    res = await session.execute(stmt)
    link = res.scalar_one_or_none()
    if not link:
        return None

    short_url = f"{base_url}/r/{link.code}"
    return LinkResponse(
        id=link.id,
        code=link.code,
        short_url=short_url,
        long_url=link.long_url,
        created_by=link.created_by,
        created_at=link.created_at,
    )


async def list_links(
    session: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    base_url: str = "http://localhost:8000"
) -> LinkListResponse:
    """Retrieve a paginated list of short links."""
    offset = (page - 1) * page_size

    # Total count query
    count_stmt = select(func.count()).select_from(Link)
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one() or 0

    # Paginated item query ordered by created_at DESC
    items_stmt = select(Link).order_by(Link.created_at.desc()).offset(offset).limit(page_size)
    items_res = await session.execute(items_stmt)
    links = items_res.scalars().all()

    items = [
        LinkResponse(
            id=link.id,
            code=link.code,
            short_url=f"{base_url}/r/{link.code}",
            long_url=link.long_url,
            created_by=link.created_by,
            created_at=link.created_at,
        )
        for link in links
    ]

    return LinkListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size
    )


async def get_link_by_code(session: AsyncSession, code: str) -> Link | None:
    """Retrieve raw Link ORM object by short_code."""
    stmt = select(Link).where(Link.code == code)
    res = await session.execute(stmt)
    return res.scalar_one_or_none()


async def get_link_by_code_and_record_click(
    session: AsyncSession,
    code: str,
    user_agent: str | None = None,
    referrer: str | None = None,
    client_ip: str | None = None
) -> str | None:
    """Indexed lookup of long_url by short_code and click event recording."""
    stmt = select(Link).where(Link.code == code)
    res = await session.execute(stmt)
    link = res.scalar_one_or_none()

    if not link:
        return None

    # Record click event
    ip_hashed = hash_ip(client_ip)
    click = ClickEvent(
        click_id=str(uuid.uuid4()),
        link_id=link.id,
        user_agent=user_agent[:500] if user_agent else None,
        referrer=referrer[:500] if referrer else None,
        ip_hash=ip_hashed,
    )
    session.add(click)
    await session.commit()

    return link.long_url


async def update_link(
    session: AsyncSession,
    link_id: uuid.UUID,
    payload: LinkUpdate,
    base_url: str = "http://localhost:8000"
) -> LinkResponse | None:
    """Update a link's target URL and invalidate its Redis cache."""
    stmt = select(Link).where(Link.id == link_id)
    res = await session.execute(stmt)
    link = res.scalar_one_or_none()
    if not link:
        return None

    if payload.long_url is not None:
        link.long_url = payload.long_url
        await session.commit()
        await session.refresh(link)
        # Invalidate cache entry immediately
        from app.services.cache_service import invalidate_redirect_cache
        await invalidate_redirect_cache(link.code)

    return LinkResponse(
        id=link.id,
        code=link.code,
        short_url=f"{base_url}/r/{link.code}",
        long_url=link.long_url,
        created_by=link.created_by,
        created_at=link.created_at,
    )


async def delete_link(session: AsyncSession, link_id: uuid.UUID) -> bool:
    """Delete a link record and invalidate its Redis cache."""
    stmt = select(Link).where(Link.id == link_id)
    res = await session.execute(stmt)
    link = res.scalar_one_or_none()
    if not link:
        return False

    code = link.code
    await session.delete(link)
    await session.commit()
    # Invalidate cache entry immediately
    from app.services.cache_service import invalidate_redirect_cache
    await invalidate_redirect_cache(code)
    return True


async def search_links(
    session: AsyncSession,
    q: str | None = None,
    sort_by: SortByEnum = SortByEnum.CREATED_AT,
    order: SortOrderEnum = SortOrderEnum.DESC,
    page: int = 1,
    page_size: int = 10,
    base_url: str = "http://localhost:8000"
) -> LinkListResponse:
    """Search and filter short links using DB-native parameterized ILIKE queries."""
    capped_page_size = min(page_size, 100)
    offset = (page - 1) * capped_page_size

    conditions = []
    if q and q.strip():
        keyword = f"%{q.strip()}%"
        conditions.append(or_(Link.code.ilike(keyword), Link.long_url.ilike(keyword)))

    # Total matching count query
    count_stmt = select(func.count()).select_from(Link)
    if conditions:
        count_stmt = count_stmt.where(and_(*conditions))
    total_res = await session.execute(count_stmt)
    total = total_res.scalar_one() or 0

    # Sorting logic with allowlisted attributes
    sort_column = Link.created_at if sort_by == SortByEnum.CREATED_AT else Link.code
    sort_order = sort_column.desc() if order == SortOrderEnum.DESC else sort_column.asc()

    # Fetch paginated items
    items_stmt = select(Link)
    if conditions:
        items_stmt = items_stmt.where(and_(*conditions))
    items_stmt = items_stmt.order_by(sort_order).offset(offset).limit(capped_page_size)

    items_res = await session.execute(items_stmt)
    links = items_res.scalars().all()

    items = [
        LinkResponse(
            id=link.id,
            code=link.code,
            short_url=f"{base_url}/r/{link.code}",
            long_url=link.long_url,
            created_by=link.created_by,
            created_at=link.created_at,
        )
        for link in links
    ]

    return LinkListResponse(
        items=items,
        total=total,
        page=page,
        page_size=capped_page_size
    )


