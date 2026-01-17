"""Retry decorators for handling transient failures."""

import asyncio
import functools
import time
from typing import Any, Callable, Type, TypeVar

from src.config import get_settings
from src.logging_config import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def retry_on_exception(
    exceptions: tuple[Type[Exception], ...],
    max_attempts: int | None = None,
    base_delay: float | None = None,
    max_delay: float | None = None,
) -> Callable[[F], F]:
    """Decorator to retry a synchronous function on specific exceptions.

    Uses exponential backoff: delay = base_delay * (2 ** attempt).

    Args:
        exceptions: Tuple of exception types to retry on.
        max_attempts: Maximum number of retry attempts (from config if None).
        base_delay: Initial delay in seconds (from config if None).
        max_delay: Maximum delay cap in seconds (from config if None).

    Returns:
        Decorated function with retry logic.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            settings = get_settings()
            attempts = max_attempts or settings.retry_max_attempts
            delay = base_delay or settings.retry_base_delay
            max_d = max_delay or settings.retry_max_delay

            last_exception = None
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < attempts - 1:  # Don't sleep on last attempt
                        wait_time = min(delay * (2**attempt), max_d)
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{attempts} for {func.__name__} "
                            f"after {type(e).__name__}: {str(e)}. "
                            f"Waiting {wait_time:.2f}s"
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"Max retry attempts ({attempts}) exceeded for {func.__name__}"
                        )

            # Raise the last exception if all attempts failed
            if last_exception:
                raise last_exception

            # This should never happen, but satisfy type checker
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def async_retry_on_exception(
    exceptions: tuple[Type[Exception], ...],
    max_attempts: int | None = None,
    base_delay: float | None = None,
    max_delay: float | None = None,
) -> Callable[[F], F]:
    """Decorator to retry an async function on specific exceptions.

    Uses exponential backoff: delay = base_delay * (2 ** attempt).

    Args:
        exceptions: Tuple of exception types to retry on.
        max_attempts: Maximum number of retry attempts (from config if None).
        base_delay: Initial delay in seconds (from config if None).
        max_delay: Maximum delay cap in seconds (from config if None).

    Returns:
        Decorated async function with retry logic.
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            settings = get_settings()
            attempts = max_attempts or settings.retry_max_attempts
            delay = base_delay or settings.retry_base_delay
            max_d = max_delay or settings.retry_max_delay

            last_exception = None
            for attempt in range(attempts):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < attempts - 1:  # Don't sleep on last attempt
                        wait_time = min(delay * (2**attempt), max_d)
                        logger.warning(
                            f"Retry attempt {attempt + 1}/{attempts} for {func.__name__} "
                            f"after {type(e).__name__}: {str(e)}. "
                            f"Waiting {wait_time:.2f}s"
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(
                            f"Max retry attempts ({attempts}) exceeded for {func.__name__}"
                        )

            # Raise the last exception if all attempts failed
            if last_exception:
                raise last_exception

            # This should never happen, but satisfy type checker
            return await func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator
