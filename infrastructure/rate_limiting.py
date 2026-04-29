"""Rate Limiting.

Provides rate limiters for API requests.
"""

import logging
import time
from threading import Lock

from domain import RateLimiterPort
from domain import RateLimitError

logger = logging.getLogger(__name__)


class SlidingWindowRateLimiter(RateLimiterPort):
    """Enforces rate limits using a sliding window algorithm."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        """Initialize rate limiter.

        Args:
            max_requests: Maximum number of requests allowed in the window.
            window_seconds: The duration of the sliding window in seconds.
        """
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._request_timestamps: list[float] = []
        self._lock = Lock()

    def enforce_rate_limit(self) -> None:
        """Record a request and check against limits.

        Raises:
            RateLimitError: If the rate limit is exceeded.
        """
        with self._lock:
            now = time.time()
            self._request_timestamps = [
                ts
                for ts in self._request_timestamps
                if now - ts <= self._window_seconds
            ]
            if len(self._request_timestamps) >= self._max_requests:
                logger.warning("Rate limit exceeded")
                raise RateLimitError("Power BI API rate limit exceeded")
            self._request_timestamps.append(now)
