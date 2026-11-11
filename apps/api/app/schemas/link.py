import uuid
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, ConfigDict


class LinkCreate(BaseModel):
    long_url: str = Field(..., description="Target long URL to shorten")
    expires_at: datetime | None = Field(
        default=None,
        description="Optional future expiration timestamp",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Optional categorization tags",
    )

    @field_validator("long_url")
    @classmethod
    def validate_long_url(cls, v: str) -> str:
        cleaned = v.strip()

        if re.search(r"[\x00-\x1f\x7f]", cleaned):
            raise ValueError(
                "URL must not contain control characters or newlines"
            )

        parsed = urlparse(cleaned)
        scheme = parsed.scheme.lower()

        if scheme not in ("http", "https"):
            raise ValueError(
                f"Invalid URL scheme '{scheme}'. "
                "Only 'http' and 'https' are allowed."
            )

        if not parsed.netloc or cleaned.startswith("//"):
            raise ValueError(
                "URL must contain a valid domain host "
                "(e.g., https://example.com)"
            )

        if parsed.username is not None or parsed.password is not None:
            raise ValueError("URL must not contain embedded user credentials")

        if "\\" in cleaned:
            raise ValueError("URL must not contain backslashes")

        return cleaned

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(
        cls, v: datetime | None
    ) -> datetime | None:
        if v is not None:
            now = datetime.now(timezone.utc)

            if v.tzinfo is None:
                v = v.replace(tzinfo=timezone.utc)

            if v <= now:
                raise ValueError(
                    "expires_at must be a future timestamp"
                )

        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        if len(v) > 10:
            raise ValueError("Maximum 10 tags allowed per link")

        for tag in v:
            if len(tag) > 30:
                raise ValueError(
                    "Each tag must be 30 characters or fewer"
                )

        return v


class LinkResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    short_url: str
    long_url: str
    created_by: str
    created_at: datetime
    expires_at: datetime | None = None
    tags: list[str] = Field(default_factory=list)


class LinkListResponse(BaseModel):
    items: list[LinkResponse]
    total: int
    page: int
    page_size: int


class LinkUpdate(BaseModel):
    long_url: str | None = Field(default=None, description="Updated target long URL")

    @field_validator("long_url")
    @classmethod
    def validate_long_url(cls, v: str | None) -> str | None:
        if v is None:
            return v
        return LinkCreate.validate_long_url(v)