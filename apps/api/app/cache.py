import logging
import time
from typing import Optional, Dict, Tuple
import redis.asyncio as redis

from app.config import settings

logger = logging.getLogger("upsk_api")

# Fallback in-memory dict cache for offline testing/environments when Redis is unreachable
_memory_cache: Dict[str, Tuple[str, float]] = {}
_memory_counters: Dict[str, Tuple[int, float]] = {}

redis_client = redis.from_url(
    settings.redis_url,
    decode_responses=True,
    socket_connect_timeout=0.5
)


async def get_cache(key: str) -> Optional[str]:
    """Retrieve string value from Redis cache with in-memory fallback if Redis is offline."""
    try:
        val = await redis_client.get(key)
        if val is not None:
            return val
    except Exception as exc:
        logger.debug(f"Redis get_cache offline for key '{key}': {exc}")

    # Fallback to in-memory cache
    if key in _memory_cache:
        val, expiry = _memory_cache[key]
        if time.time() < expiry:
            return val
        else:
            del _memory_cache[key]
    return None


async def set_cache(key: str, value: str, ttl_seconds: int = 300) -> bool:
    """Store string value in Redis cache with TTL and in-memory fallback."""
    expiry = time.time() + ttl_seconds
    _memory_cache[key] = (value, expiry)
    try:
        await redis_client.set(key, value, ex=ttl_seconds)
        return True
    except Exception as exc:
        logger.debug(f"Redis set_cache offline for key '{key}': {exc}")
        return True


async def delete_cache(key: str) -> bool:
    """Invalidate string key from Redis cache and in-memory fallback."""
    if key in _memory_cache:
        del _memory_cache[key]
    try:
        await redis_client.delete(key)
        return True
    except Exception as exc:
        logger.debug(f"Redis delete_cache offline for key '{key}': {exc}")
        return True


async def incr_cache_with_ttl(key: str, ttl_seconds: int = 60) -> Optional[int]:
    """Atomically increment a counter key with TTL in Redis and in-memory fallback."""
    try:
        async with redis_client.pipeline(transaction=True) as pipe:
            pipe.incr(key)
            pipe.ttl(key)
            results = await pipe.execute()
            count = results[0]
            current_ttl = results[1]
            if current_ttl == -1 or current_ttl is None:
                await redis_client.expire(key, ttl_seconds)
            return count
    except Exception as exc:
        logger.debug(f"Redis incr_cache_with_ttl offline for key '{key}': {exc}")

    # Fallback to in-memory counters
    now = time.time()
    if key in _memory_counters:
        count, expiry = _memory_counters[key]
        if now < expiry:
            count += 1
            _memory_counters[key] = (count, expiry)
            return count

    # Reset / New counter
    _memory_counters[key] = (1, now + ttl_seconds)
    return 1
