"""Rate Limiting Middleware.

Limits request frequency using a sliding window / token bucket algorithm.
"""

from __future__ import annotations

import math
import time
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Token-bucket rate limiter middleware.
    Limits request frequency per client IP address.
    """

    def __init__(self, app, rate_limit: int = 100, period: int = 60) -> None:
        super().__init__(app)
        self.rate_limit = rate_limit
        self.period = period
        self.refill_rate = rate_limit / period  # tokens per second
        self.buckets: dict[str, tuple[float, float]] = {}  # ip -> (tokens, last_updated)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Only rate limit API requests
        if not request.url.path.startswith("/api"):
            return await call_next(request)

        client_ip = request.client.host if request.client else "127.0.0.1"
        now = time.time()

        # Get or initialize bucket
        if client_ip not in self.buckets:
            self.buckets[client_ip] = (float(self.rate_limit), now)

        tokens, last_updated = self.buckets[client_ip]

        # Refill tokens based on elapsed time
        elapsed = now - last_updated
        refilled_tokens = elapsed * self.refill_rate
        new_tokens = min(float(self.rate_limit), tokens + refilled_tokens)

        # Check token count
        if new_tokens >= 1:
            tokens = new_tokens - 1
            self.buckets[client_ip] = (tokens, now)

            response = await call_next(request)

            # Inject rate limiting response headers
            response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
            response.headers["X-RateLimit-Remaining"] = str(max(0, math.floor(tokens)))
            return response
        else:
            self.buckets[client_ip] = (new_tokens, now)
            logger.warning("rate_limit_exceeded", ip=client_ip, path=str(request.url.path))

            retry_after = max(1, math.ceil((1.0 - new_tokens) / self.refill_rate))

            response = JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
            )
            response.headers["Retry-After"] = str(retry_after)
            response.headers["X-RateLimit-Limit"] = str(self.rate_limit)
            response.headers["X-RateLimit-Remaining"] = "0"
            return response
