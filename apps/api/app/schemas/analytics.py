import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class LinkAnalyticsResponse(BaseModel):
    """Analytics summary response for a specific short link within a time window."""
    link_id: uuid.UUID
    code: str
    total_clicks: int = Field(..., ge=0, description="Total number of recorded click events")
    last_clicked_at: Optional[datetime] = Field(None, description="Timestamp of the most recent click")
    window_from: datetime
    window_to: datetime


class PurgeAnalyticsResponse(BaseModel):
    """Response payload for administrative analytics retention purge."""
    retention_days: int
    purged_count: int
    cutoff_timestamp: datetime
