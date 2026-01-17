"""Tests for rate limiting middleware."""

import asyncio

import pytest
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient

from src.config import Settings
from src.middleware.rate_limit import RateLimitMiddleware


@pytest.fixture
def app_with_rate_limit():
    """Create a test app with rate limiting."""
    app = FastAPI()

    # Add rate limiting middleware
    app.add_middleware(RateLimitMiddleware)

    @app.get("/test")
    def test_endpoint():
        return {"message": "success"}

    @app.get("/api/health")
    def health_endpoint():
        return {"status": "healthy"}

    return app


@pytest.fixture
def client(app_with_rate_limit):
    """Create a test client."""
    return TestClient(app_with_rate_limit)


@pytest.fixture
def settings_low_limit(monkeypatch):
    """Create settings with low rate limit for testing."""
    # Mock settings with low limits
    test_settings = Settings(
        data_dir="data",
        rate_limit_requests=3,
        rate_limit_window_seconds=60,
    )

    # Patch get_settings to return our test settings
    from src import config
    monkeypatch.setattr(config, "get_settings", lambda: test_settings)

    return test_settings


def test_normal_traffic_allowed(client):
    """Test that normal traffic is allowed."""
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "success"}


def test_rate_limit_headers_present(client):
    """Test that rate limit headers are added to responses."""
    response = client.get("/test")

    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers


def test_health_endpoint_not_rate_limited(client, settings_low_limit):
    """Test that health check endpoint is not rate limited."""
    # Make many requests to health endpoint
    for _ in range(10):
        response = client.get("/api/health")
        assert response.status_code == 200


def test_rate_limit_exceeded(client, settings_low_limit):
    """Test that excessive requests are blocked."""
    # Make requests up to the limit
    for i in range(3):
        response = client.get("/test")
        assert response.status_code == 200

    # Next request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429

    # Check error response
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"]
    assert "Rate limit exceeded" in data["detail"]["error"]


def test_rate_limit_remaining_decreases(client, settings_low_limit):
    """Test that X-RateLimit-Remaining decreases with each request."""
    response1 = client.get("/test")
    remaining1 = int(response1.headers["X-RateLimit-Remaining"])

    response2 = client.get("/test")
    remaining2 = int(response2.headers["X-RateLimit-Remaining"])

    assert remaining2 < remaining1
    assert remaining1 - remaining2 == 1


def test_rate_limit_per_ip(client, settings_low_limit):
    """Test that rate limiting is per IP address."""
    # This test is limited because TestClient doesn't easily
    # support different IPs, but we can verify the basic mechanism
    for i in range(3):
        response = client.get("/test")
        assert response.status_code == 200

    # Fourth request should fail
    response = client.get("/test")
    assert response.status_code == 429


def test_rate_limit_error_includes_reset_time(client, settings_low_limit):
    """Test that rate limit error includes reset time."""
    # Exhaust the rate limit
    for _ in range(3):
        client.get("/test")

    # Get rate limited
    response = client.get("/test")
    assert response.status_code == 429

    data = response.json()
    assert "detail" in data
    assert "reset_at" in data["detail"]
    assert isinstance(data["detail"]["reset_at"], int)


def test_rate_limit_includes_window_info(client, settings_low_limit):
    """Test that rate limit error includes window information."""
    # Exhaust the rate limit
    for _ in range(3):
        client.get("/test")

    # Get rate limited
    response = client.get("/test")
    assert response.status_code == 429

    data = response.json()
    assert "detail" in data
    assert "limit" in data["detail"]
    assert "window_seconds" in data["detail"]
    assert data["detail"]["limit"] == 3
    assert data["detail"]["window_seconds"] == 60


@pytest.mark.asyncio
async def test_rate_limit_sliding_window():
    """Test that the sliding window works correctly."""
    from src.middleware.rate_limit import RateLimitMiddleware
    from unittest.mock import AsyncMock, MagicMock

    # Create middleware
    app = FastAPI()
    middleware = RateLimitMiddleware(app)
    middleware.settings.rate_limit_requests = 2
    middleware.settings.rate_limit_window_seconds = 1  # 1 second window

    # Mock request and call_next
    request = MagicMock()
    request.url.path = "/test"
    request.client.host = "127.0.0.1"

    async def mock_call_next(req):
        response = Response()
        return response

    # First two requests should succeed
    response1 = await middleware.dispatch(request, mock_call_next)
    assert response1.status_code == 200

    response2 = await middleware.dispatch(request, mock_call_next)
    assert response2.status_code == 200

    # Third request should fail (rate limited)
    with pytest.raises(Exception):  # HTTPException
        await middleware.dispatch(request, mock_call_next)

    # Wait for window to expire
    await asyncio.sleep(1.1)

    # Should work again after window expires
    # (This is simplified - in reality the sliding window would allow
    # requests as old ones expire)
    response4 = await middleware.dispatch(request, mock_call_next)
    assert response4.status_code == 200
