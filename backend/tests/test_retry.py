"""Tests for retry logic."""

import asyncio

import pytest

from src.utils.retry import async_retry_on_exception, retry_on_exception


class TransientError(Exception):
    """Test exception for transient failures."""
    pass


class PermanentError(Exception):
    """Test exception for permanent failures."""
    pass


def test_retry_success_first_try():
    """Test successful operation on first attempt."""
    call_count = 0

    @retry_on_exception((TransientError,), max_attempts=3)
    def operation():
        nonlocal call_count
        call_count += 1
        return "success"

    result = operation()
    assert result == "success"
    assert call_count == 1


def test_retry_eventual_success():
    """Test operation succeeds after retries."""
    call_count = 0

    @retry_on_exception((TransientError,), max_attempts=3, base_delay=0.01)
    def operation():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransientError("Transient failure")
        return "success"

    result = operation()
    assert result == "success"
    assert call_count == 3


def test_retry_max_attempts_exceeded():
    """Test max retry attempts are respected."""
    call_count = 0

    @retry_on_exception((TransientError,), max_attempts=3, base_delay=0.01)
    def operation():
        nonlocal call_count
        call_count += 1
        raise TransientError("Always fails")

    with pytest.raises(TransientError):
        operation()

    assert call_count == 3


def test_retry_wrong_exception_not_retried():
    """Test operation is not retried for non-specified exceptions."""
    call_count = 0

    @retry_on_exception((TransientError,), max_attempts=3)
    def operation():
        nonlocal call_count
        call_count += 1
        raise PermanentError("Different error")

    with pytest.raises(PermanentError):
        operation()

    # Should fail immediately without retry
    assert call_count == 1


def test_retry_multiple_exception_types():
    """Test retry works with multiple exception types."""
    call_count = 0

    @retry_on_exception((TransientError, IOError), max_attempts=3, base_delay=0.01)
    def operation():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise TransientError("First error")
        elif call_count == 2:
            raise IOError("Second error")
        return "success"

    result = operation()
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_async_retry_success_first_try():
    """Test async successful operation on first attempt."""
    call_count = 0

    @async_retry_on_exception((TransientError,), max_attempts=3)
    async def operation():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await operation()
    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_async_retry_eventual_success():
    """Test async operation succeeds after retries."""
    call_count = 0

    @async_retry_on_exception((TransientError,), max_attempts=3, base_delay=0.01)
    async def operation():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise TransientError("Transient failure")
        return "success"

    result = await operation()
    assert result == "success"
    assert call_count == 3


@pytest.mark.asyncio
async def test_async_retry_max_attempts_exceeded():
    """Test async max retry attempts are respected."""
    call_count = 0

    @async_retry_on_exception((TransientError,), max_attempts=3, base_delay=0.01)
    async def operation():
        nonlocal call_count
        call_count += 1
        raise TransientError("Always fails")

    with pytest.raises(TransientError):
        await operation()

    assert call_count == 3


@pytest.mark.asyncio
async def test_async_retry_wrong_exception_not_retried():
    """Test async operation is not retried for non-specified exceptions."""
    call_count = 0

    @async_retry_on_exception((TransientError,), max_attempts=3)
    async def operation():
        nonlocal call_count
        call_count += 1
        raise PermanentError("Different error")

    with pytest.raises(PermanentError):
        await operation()

    # Should fail immediately without retry
    assert call_count == 1


def test_retry_exponential_backoff():
    """Test that retry delay increases exponentially."""
    import time

    call_times = []

    @retry_on_exception((TransientError,), max_attempts=3, base_delay=0.1, max_delay=1.0)
    def operation():
        call_times.append(time.time())
        if len(call_times) < 3:
            raise TransientError("Retry me")
        return "success"

    operation()

    # Verify delays increase (approximately)
    # First retry: ~0.1s, second retry: ~0.2s
    if len(call_times) >= 3:
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        # Second delay should be roughly double the first
        assert delay2 > delay1
