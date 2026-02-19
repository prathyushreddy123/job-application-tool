import asyncio
import time
from urllib.parse import urlparse


class RateLimiter:
    """Per-domain rate limiter for job application submissions.

    Tracks request timestamps per domain and blocks if the rate limit
    (requests per hour) would be exceeded.
    """

    def __init__(self, rate_limits: dict[str, int]):
        """Initialize with rate limits.

        Args:
            rate_limits: Mapping of domain -> max requests per hour.
                         Use "default" key for fallback limit.
        """
        self._limits = rate_limits
        self._timestamps: dict[str, list[float]] = {}

    def _get_domain(self, url: str) -> str:
        """Extract the registrable domain from a URL."""
        try:
            hostname = urlparse(url).hostname or ""
            if not hostname:
                return "unknown"
            # Simplify: use last two parts (e.g., greenhouse.io)
            parts = hostname.split(".")
            if len(parts) >= 2:
                return ".".join(parts[-2:])
            return hostname
        except Exception:
            return "unknown"

    def _get_limit(self, domain: str) -> int:
        """Get the rate limit for a domain."""
        if domain in self._limits:
            return self._limits[domain]
        return self._limits.get("default", 5)

    def _prune_old(self, domain: str):
        """Remove timestamps older than 1 hour."""
        cutoff = time.time() - 3600
        if domain in self._timestamps:
            self._timestamps[domain] = [
                t for t in self._timestamps[domain] if t > cutoff
            ]

    def can_proceed(self, url: str) -> bool:
        """Check if a request to this URL's domain is within rate limits."""
        domain = self._get_domain(url)
        self._prune_old(domain)
        limit = self._get_limit(domain)
        current = len(self._timestamps.get(domain, []))
        return current < limit

    def seconds_until_available(self, url: str) -> float:
        """Return seconds to wait before next request is allowed. 0 if available now."""
        domain = self._get_domain(url)
        self._prune_old(domain)
        limit = self._get_limit(domain)
        timestamps = self._timestamps.get(domain, [])

        if len(timestamps) < limit:
            return 0.0

        # Wait until the oldest timestamp expires (1 hour window)
        oldest = min(timestamps)
        wait = (oldest + 3600) - time.time()
        return max(0.0, wait)

    async def wait_if_needed(self, url: str):
        """Block until the domain's rate limit allows a new request."""
        wait_time = self.seconds_until_available(url)
        if wait_time > 0:
            await asyncio.sleep(wait_time)

    def record(self, url: str):
        """Record that a request was made to this URL's domain."""
        domain = self._get_domain(url)
        if domain not in self._timestamps:
            self._timestamps[domain] = []
        self._timestamps[domain].append(time.time())

    def get_status(self) -> dict[str, dict]:
        """Return current rate limit status for all tracked domains."""
        status = {}
        for domain in self._timestamps:
            self._prune_old(domain)
            limit = self._get_limit(domain)
            current = len(self._timestamps.get(domain, []))
            status[domain] = {
                "used": current,
                "limit": limit,
                "available": limit - current,
            }
        return status
