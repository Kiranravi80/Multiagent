"""PAIOS Retry Engine.

Executes asynchronous operations with configurable retry policies
(fixed, exponential, and backoff with jitter).
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Callable, Coroutine
from typing import Any, TypeVar

from app.core.logging import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RetryEngine:
    """Utility to execute async functions with robust retry behaviors."""

    @staticmethod
    async def retry_async(
        func: Callable[[], Coroutine[Any, Any, T]],
        *,
        max_retries: int = 3,
        strategy: str = "exponential_backoff_with_jitter",
        base_delay_seconds: float = 1.0,
        max_delay_seconds: float = 60.0,
        backoff_factor: float = 2.0,
        retryable_exceptions: tuple[type[BaseException], ...] = (Exception,),
        operation_name: str = "anonymous_operation",
    ) -> T:
        """Execute an async function with retries.

        Args:
            func: The async callable to execute.
            max_retries: Maximum number of retry attempts.
            strategy: Delay calculation strategy: 'fixed', 'exponential_backoff',
                      or 'exponential_backoff_with_jitter'.
            base_delay_seconds: Base/initial delay in seconds.
            max_delay_seconds: Maximum delay ceiling in seconds.
            backoff_factor: Multiplier for exponential backoff.
            retryable_exceptions: Exception classes that trigger a retry.
            operation_name: Label used in logging.

        Returns:
            The successful result of the async function.

        Raises:
            exc: The last encountered exception if all retry attempts fail.
        """
        retries = 0
        while True:
            try:
                return await func()
            except retryable_exceptions as exc:
                retries += 1
                if retries > max_retries:
                    logger.error(
                        "retry_limit_reached",
                        operation=operation_name,
                        retries=retries - 1,
                        error=str(exc),
                    )
                    raise exc

                # Calculate delay
                if strategy == "fixed":
                    delay = base_delay_seconds
                elif strategy == "exponential_backoff":
                    delay = min(base_delay_seconds * (backoff_factor ** (retries - 1)), max_delay_seconds)
                else:  # exponential_backoff_with_jitter
                    exponential_delay = min(base_delay_seconds * (backoff_factor ** (retries - 1)), max_delay_seconds)
                    # Add random jitter: 50% to 150% of the calculated delay
                    delay = exponential_delay * random.uniform(0.5, 1.5)

                logger.warning(
                    "retry_triggering",
                    operation=operation_name,
                    attempt=retries,
                    max_retries=max_retries,
                    delay_seconds=round(delay, 2),
                    error=str(exc),
                )
                await asyncio.sleep(delay)
