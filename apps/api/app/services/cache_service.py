import logging
from typing import Optional
from app.cache import delete_cache, get_cache, incr_cache_with_ttl, set_cache

logger = logging.getLogger("upsk_api")

REDIRECT_CACHE_TTL = 300  # 5 minutes
RATE_LIMIT_WINDOW = 60    # 60 seconds
DEFAULT_RATE_LIMIT = 60    # 60 requests per minute per IP


async def get_redirect_cache(code: str) -> Optional[str]:
    """Fetch cached target URL for short code."""
    key = f"redirect:{code}"
    return await get_cache(key)


async def set_redirect_cache(code: str, long_url: str, ttl_seconds: int = REDIRECT_CACHE_TTL) -> bool:
    """Cache target URL for short code with TTL."""
    key = f"redirect:{code}"
    return await set_cache(key, long_url, ttl_seconds=ttl_seconds)


async def invalidate_redirect_cache(code: str) -> bool:
    """Invalidate cached target URL when link is updated or deleted."""
    key = f"redirect:{code}"
    return await delete_cache(key)


async def check_redirect_rate_limit(
    client_ip: str,
    max_requests: int = DEFAULT_RATE_LIMIT,
    window_seconds: int = RATE_LIMIT_WINDOW
) -> bool:
    """Check if request rate for IP is within limits. Returns True if allowed, False if throttled."""
    if not client_ip:
        return True

    key = f"rate_limit:redirect:{client_ip}"
    current_count = await incr_cache_with_ttl(key, ttl_seconds=window_seconds)

    # Fail open if Redis is unreachable
    if current_count is None:
        return True

    if current_count > max_requests:
        logger.warning(f"Rate limit exceeded for IP '{client_ip}': {current_count}/{max_requests}")
        return False

    return True
