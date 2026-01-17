"""Rate limiting middleware using in-memory sliding window."""

import time
from collections import defaultdict
from typing import Callable

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.config import get_settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory rate limiter using sliding window algorithm."""

    def __init__(self, app):
        """Initialize rate limiter.

        Args:
            app: The FastAPI application.
        """
        super().__init__(app)
        # Dict mapping client IP to list of request timestamps
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.settings = get_settings()

    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """Apply rate limiting to requests.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            The HTTP response.

        Raises:
            HTTPException: 429 if rate limit exceeded.
        """
        # Skip rate limiting for health checks
        if request.url.path == "/api/health":
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"

        # Current timestamp
        now = time.time()

        # Get client's request history
        client_requests = self.requests[client_ip]

        # Remove requests outside the current window
        window_start = now - self.settings.rate_limit_window_seconds
        client_requests[:] = [ts for ts in client_requests if ts > window_start]

        # Check if limit exceeded
        if len(client_requests) >= self.settings.rate_limit_requests:
            # Calculate when the oldest request will expire
            oldest_request = client_requests[0]
            reset_time = int(oldest_request + self.settings.rate_limit_window_seconds)

            raise HTTPException(
                status_code=429,
                detail={
                    "error": "Rate limit exceeded",
                    "limit": self.settings.rate_limit_requests,
                    "window_seconds": self.settings.rate_limit_window_seconds,
                    "reset_at": reset_time,
                },
            )

        # Add current request to history
        client_requests.append(now)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.settings.rate_limit_requests)
        response.headers["X-RateLimit-Remaining"] = str(
            self.settings.rate_limit_requests - len(client_requests)
        )
        response.headers["X-RateLimit-Reset"] = str(
            int(now + self.settings.rate_limit_window_seconds)
        )

        return response
