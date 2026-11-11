import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies.auth import verify_api_key
from app.schemas.link import LinkCreate, LinkResponse, LinkListResponse, LinkUpdate
from app.schemas.analytics import LinkAnalyticsResponse, PurgeAnalyticsResponse
from app.schemas.search import SortByEnum, SortOrderEnum
from app.services import links_service, analytics_service

# All administrative /links endpoints require X-API-Key authentication
router = APIRouter(
    prefix="/links",
    tags=["Links"],
    dependencies=[Depends(verify_api_key)]
)


@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link_endpoint(
    payload: LinkCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new short link with validated target URL."""
    return await links_service.create_link(session=db, payload=payload)


@router.get("", response_model=LinkListResponse, status_code=status.HTTP_200_OK)
async def list_links_endpoint(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve a paginated list of short links."""
    return await links_service.list_links(session=db, page=page, page_size=page_size)


@router.get("/search", response_model=LinkListResponse, status_code=status.HTTP_200_OK)
async def search_links_endpoint(
    q: Optional[str] = Query(None, description="Search keyword matching short code or long target URL"),
    sort_by: SortByEnum = Query(SortByEnum.CREATED_AT, description="Field to sort by (created_at, code)"),
    order: SortOrderEnum = Query(SortOrderEnum.DESC, description="Sort order direction (asc, desc)"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=10, ge=1, le=100, description="Items per page (max 100)"),
    db: AsyncSession = Depends(get_db)
):
    """Search and filter short links with allowlisted parameters and bounded pagination."""
    return await links_service.search_links(
        session=db,
        q=q,
        sort_by=sort_by,
        order=order,
        page=page,
        page_size=page_size
    )


@router.delete("/analytics/purge", response_model=PurgeAnalyticsResponse, status_code=status.HTTP_200_OK)
async def purge_analytics_endpoint(
    retention_days: int = Query(default=30, ge=0, description="Number of retention days"),
    db: AsyncSession = Depends(get_db)
):
    """Purge historical click events older than retention cutoff (protected admin endpoint)."""
    return await analytics_service.purge_old_clicks(session=db, retention_days=retention_days)


@router.get("/{link_id}", response_model=LinkResponse, status_code=status.HTTP_200_OK)
async def get_link_endpoint(
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve details for a single link by UUID."""
    link = await links_service.get_link_by_id(session=db, link_id=link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    return link


@router.get("/{link_id}/analytics", response_model=LinkAnalyticsResponse, status_code=status.HTTP_200_OK)
async def get_link_analytics_endpoint(
    link_id: uuid.UUID,
    window_from: Optional[datetime] = Query(None, alias="from"),
    window_to: Optional[datetime] = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve protected click analytics for a specific short link within a time window."""
    return await analytics_service.get_link_analytics(
        session=db,
        link_id=link_id,
        from_time=window_from,
        to_time=window_to
    )


@router.patch("/{link_id}", response_model=LinkResponse, status_code=status.HTTP_200_OK)
async def update_link_endpoint(
    link_id: uuid.UUID,
    payload: LinkUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update a short link target URL and invalidate its cache entry."""
    updated = await links_service.update_link(session=db, link_id=link_id, payload=payload)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    return updated


@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[])
async def delete_link_endpoint(
    link_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete a short link record and invalidate its cache entry."""
    deleted = await links_service.delete_link(session=db, link_id=link_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Link not found"
        )
    return None
