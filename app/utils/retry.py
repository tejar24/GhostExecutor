"""
Retry Utilities

Provides retry logic with exponential backoff for handling transient failures.
"""

import asyncio
import functools
import random
import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Type, TypeVar, Union

from .logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_attempts: int = 3
    base_delay: float = 1.0  # seconds
    max_delay: float = 60.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.1
    retry_exceptions: List[Type[Exception]] = field(
        default_factory=lambda: [Exception]
    )
    on_retry: Optional[Callable[[Exception, int], None]] = None


def calculate_delay(
    attempt: int,
    config: RetryConfig,
) -> float:
    """
    Calculate delay before next retry attempt.

    Args:
        attempt: Current attempt number (1-indexed)
        config: Retry configuration

    Returns:
        Delay in seconds
    """
    delay = config.base_delay * (config.exponential_base ** (attempt - 1))
    delay = min(delay, config.max_delay)

    if config.jitter:
        jitter_range = delay * config.jitter_factor
        delay += random.uniform(-jitter_range, jitter_range)

    return max(0, delay)


def should_retry(exception: Exception, config: RetryConfig) -> bool:
    """
    Check if an exception should trigger a retry.

    Args:
        exception: The exception that occurred
        config: Retry configuration

    Returns:
        True if retry should be attempted
    """
    return any(
        isinstance(exception, exc_type)
        for exc_type in config.retry_exceptions
    )


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    max_attempts: Optional[int] = None,
    base_delay: Optional[float] = None,
    exceptions: Optional[List[Type[Exception]]] = None,
) -> Callable:
    """
    Decorator for retrying functions with exponential backoff.

    Can be used with or without arguments:
        @retry_with_backoff
        def func(): ...

        @retry_with_backoff(max_attempts=5)
        def func(): ...

    Args:
        config: Full retry configuration
        max_attempts: Maximum retry attempts (overrides config)
        base_delay: Base delay between retries (overrides config)
        exceptions: Exception types to retry on (overrides config)

    Returns:
        Decorated function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            retry_config = config or RetryConfig()

            # Apply overrides
            if max_attempts is not None:
                retry_config.max_attempts = max_attempts
            if base_delay is not None:
                retry_config.base_delay = base_delay
            if exceptions is not None:
                retry_config.retry_exceptions = exceptions

            last_exception: Optional[Exception] = None

            for attempt in range(1, retry_config.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if not should_retry(e, retry_config):
                        raise

                    if attempt == retry_config.max_attempts:
                        logger.error(
                            f"All {retry_config.max_attempts} attempts failed "
                            f"for {func.__name__}: {e}"
                        )
                        raise

                    delay = calculate_delay(attempt, retry_config)
                    logger.warning(
                        f"Attempt {attempt}/{retry_config.max_attempts} failed "
                        f"for {func.__name__}: {e}. Retrying in {delay:.2f}s..."
                    )

                    if retry_config.on_retry:
                        retry_config.on_retry(e, attempt)

                    time.sleep(delay)

            # Should not reach here, but for type safety
            if last_exception:
                raise last_exception
            raise RuntimeError("Unexpected state in retry logic")

        return wrapper

    # Handle both @retry_with_backoff and @retry_with_backoff() syntax
    if config is not None and callable(config):
        # Called as @retry_with_backoff without parentheses
        func = config
        config = None
        return decorator(func)

    return decorator


async def async_retry_with_backoff(
    func: Callable[..., T],
    *args: Any,
    config: Optional[RetryConfig] = None,
    **kwargs: Any,
) -> T:
    """
    Async version of retry with backoff.

    Args:
        func: Async function to retry
        *args: Function arguments
        config: Retry configuration
        **kwargs: Function keyword arguments

    Returns:
        Function result
    """
    retry_config = config or RetryConfig()
    last_exception: Optional[Exception] = None

    for attempt in range(1, retry_config.max_attempts + 1):
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            last_exception = e

            if not should_retry(e, retry_config):
                raise

            if attempt == retry_config.max_attempts:
                logger.error(
                    f"All {retry_config.max_attempts} async attempts failed "
                    f"for {func.__name__}: {e}"
                )
                raise

            delay = calculate_delay(attempt, retry_config)
            logger.warning(
                f"Async attempt {attempt}/{retry_config.max_attempts} failed "
                f"for {func.__name__}: {e}. Retrying in {delay:.2f}s..."
            )

            if retry_config.on_retry:
                retry_config.on_retry(e, attempt)

            await asyncio.sleep(delay)

    if last_exception:
        raise last_exception
    raise RuntimeError("Unexpected state in async retry logic")


class RetryContext:
    """
    Context manager for retry logic.

    Usage:
        async with RetryContext(max_attempts=3) as retry:
            while retry.should_continue():
                try:
                    result = await do_something()
                    break
                except Exception as e:
                    await retry.handle_error(e)
    """

    def __init__(self, config: Optional[RetryConfig] = None, **kwargs: Any):
        self.config = config or RetryConfig(**kwargs)
        self.attempt = 0
        self.last_error: Optional[Exception] = None

    def __enter__(self) -> "RetryContext":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        return False

    async def __aenter__(self) -> "RetryContext":
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        return False

    def should_continue(self) -> bool:
        """Check if more attempts should be made."""
        return self.attempt < self.config.max_attempts

    def handle_error(self, error: Exception) -> None:
        """
        Handle an error synchronously.

        Args:
            error: The exception that occurred
        """
        self.last_error = error
        self.attempt += 1

        if not should_retry(error, self.config):
            raise error

        if self.attempt >= self.config.max_attempts:
            raise error

        delay = calculate_delay(self.attempt, self.config)
        logger.warning(
            f"Attempt {self.attempt}/{self.config.max_attempts} failed: {error}. "
            f"Retrying in {delay:.2f}s..."
        )

        if self.config.on_retry:
            self.config.on_retry(error, self.attempt)

        time.sleep(delay)

    async def handle_error_async(self, error: Exception) -> None:
        """
        Handle an error asynchronously.

        Args:
            error: The exception that occurred
        """
        self.last_error = error
        self.attempt += 1

        if not should_retry(error, self.config):
            raise error

        if self.attempt >= self.config.max_attempts:
            raise error

        delay = calculate_delay(self.attempt, self.config)
        logger.warning(
            f"Attempt {self.attempt}/{self.config.max_attempts} failed: {error}. "
            f"Retrying in {delay:.2f}s..."
        )

        if self.config.on_retry:
            self.config.on_retry(error, self.attempt)

        await asyncio.sleep(delay)
