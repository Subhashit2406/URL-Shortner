import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Link(Base):
    __tablename__ = "links"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False
    )
    long_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str] = mapped_column(
        String(100),
        index=True,
        nullable=False,
        default="anonymous"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    # Relationship to ClickEvent
    clicks: Mapped[list["ClickEvent"]] = relationship(
        "ClickEvent",
        back_populates="link",
        cascade="all, delete-orphan"
    )


class ClickEvent(Base):
    __tablename__ = "click_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    click_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        default=lambda: str(uuid.uuid4())
    )
    link_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("links.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    ip_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Relationship to Link
    link: Mapped["Link"] = relationship("Link", back_populates="clicks")


# Compound Index for efficient analytics queries filtering by link + time
Index("idx_click_events_link_time", ClickEvent.link_id, ClickEvent.clicked_at)
