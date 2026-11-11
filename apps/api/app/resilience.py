import asyncio
import logging
import random
import time
from enum import Enum
from typing import Callable, Any

logger = logging.getLogger("upsk_api")


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerError(Exception):
    pass


class CircuitBreaker:
    def __init__(
        self,
        name: str = "default_dependency",
        fail_max: int = 5,
        reset_timeout: float = 30.0,
        request_timeout: float = 2.0,
    ):
        self.name = name
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.request_timeout = request_timeout

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()
        self._lock = asyncio.Lock()

    async def __call__(self, func: Callable, *args, **kwargs) -> Any:
        async with self._lock:
            now = time.time()
            if self.state == CircuitState.OPEN:
                if now - self.last_state_change > self.reset_timeout:
                    self.state = CircuitState.HALF_OPEN
                    self.last_state_change = now
                    logger.info(
                        "circuit_half_open",
                        extra={"dependency": self.name, "old_state": "open", "new_state": "half_open"},
                    )
                else:
                    logger.warning(
                        "circuit_open_fallback",
                        extra={"dependency": self.name, "state": "open"},
                    )
                    raise CircuitBreakerError(f"Circuit breaker '{self.name}' is OPEN")

        try:
            res = await asyncio.wait_for(func(*args, **kwargs), timeout=self.request_timeout)
        except asyncio.TimeoutError as err:
            await self._on_failure()
            logger.warning(
                "dependency_timeout",
                extra={
                    "dependency": self.name,
                    "timeout_ms": int(self.request_timeout * 1000),
                    "error": "TimeoutError",
                },
            )
            raise err
        except Exception as err:
            await self._on_failure()
            raise err

        await self._on_success()
        return res

    async def _on_success(self):
        async with self._lock:
            if self.state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
                logger.info(
                    "circuit_closed",
                    extra={"dependency": self.name, "old_state": self.state.value, "new_state": "closed"},
                )
            self.state = CircuitState.CLOSED
            self.failure_count = 0

    async def _on_failure(self):
        async with self._lock:
            self.failure_count += 1
            if self.failure_count >= self.fail_max or self.state == CircuitState.HALF_OPEN:
                if self.state != CircuitState.OPEN:
                    logger.error(
                        "circuit_opened",
                        extra={"dependency": self.name, "failure_count": self.failure_count, "state": "open"},
                    )
                self.state = CircuitState.OPEN
                self.last_state_change = time.time()


async def retry_with_backoff(
    fn: Callable,
    max_retries: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 2.0,
    jitter: float = 0.05,
    retryable_exceptions: tuple = (ConnectionError, asyncio.TimeoutError, OSError),
):
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except retryable_exceptions as e:
            last_error = e
            if attempt == max_retries:
                break

            exponential_delay = min(base_delay * (2 ** attempt), max_delay)
            jitter_offset = random.uniform(-jitter, jitter)
            delay = max(0, exponential_delay + jitter_offset)

            logger.warning(
                "retry_attempt",
                extra={
                    "attempt": attempt + 1,
                    "max_retries": max_retries,
                    "delay_ms": round(delay * 1000, 2),
                    "error_type": type(e).__name__,
                },
            )
            await asyncio.sleep(delay)
        except Exception:
            raise

    if last_error:
        raise last_error
