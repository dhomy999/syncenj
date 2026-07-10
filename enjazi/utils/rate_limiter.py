import time
import random
from enjazi.utils.logger import logger


class RateLimiter:
    """Simple delay-based rate limiter with jitter."""

    def __init__(self, base_delay: float = 1.5, jitter: float = 2.0):
        self.base_delay = base_delay
        self.jitter = jitter
        self._last_request_at: float = 0.0

    def wait(self) -> None:
        """Wait the required delay since the last request."""
        elapsed = time.monotonic() - self._last_request_at
        delay = self.base_delay + random.uniform(0, self.jitter)
        remaining = delay - elapsed
        if remaining > 0:
            logger.debug(f"Rate limiter: sleeping {remaining:.2f}s")
            time.sleep(remaining)
        self._last_request_at = time.monotonic()
