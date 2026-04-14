"""
Shared async retry utility with exponential backoff.

Usage:
    result = await retry_async(lambda: some_async_fn(), max_retries=3)
"""

import asyncio
import logging
from typing import TypeVar, Callable, Awaitable

logger = logging.getLogger("leadfactory.retry")

T = TypeVar("T")


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    max_retries: int = 3,
    backoff_base: float = 1.0,
    retryable_exceptions: tuple = (Exception,),
) -> T:
    """
    Retry an async callable with exponential backoff.

    Args:
        fn: Async callable (no arguments) to retry.
        max_retries: Maximum number of retry attempts.
        backoff_base: Base delay in seconds (doubled each retry).
        retryable_exceptions: Tuple of exception types that trigger a retry.

    Returns:
        The result of the callable on success.

    Raises:
        The last exception if all retries are exhausted.
    """
    last_exc: Exception | None = None
    for attempt in range(max_retries + 1):
        try:
            return await fn()
        except retryable_exceptions as e:
            last_exc = e
            if attempt == max_retries:
                break
            wait = backoff_base * (2 ** attempt)
            logger.warning(
                "Retry %d/%d after %.1fs: %s", attempt + 1, max_retries, wait, e
            )
            await asyncio.sleep(wait)
    raise last_exc  # type: ignore[misc]
