import time

import pytest

from backend.automation.rate_limiter import RateLimiter


class TestRateLimiter:
    def test_can_proceed_under_limit(self):
        rl = RateLimiter({"greenhouse.io": 3, "default": 5})
        assert rl.can_proceed("https://boards.greenhouse.io/test/jobs/1") is True

    def test_can_proceed_at_limit(self):
        rl = RateLimiter({"greenhouse.io": 2, "default": 5})
        rl.record("https://boards.greenhouse.io/a/jobs/1")
        rl.record("https://boards.greenhouse.io/b/jobs/2")
        assert rl.can_proceed("https://boards.greenhouse.io/c/jobs/3") is False

    def test_default_limit_used_for_unknown_domain(self):
        rl = RateLimiter({"default": 1})
        assert rl.can_proceed("https://careers.example.com/apply") is True
        rl.record("https://careers.example.com/apply")
        assert rl.can_proceed("https://careers.example.com/apply2") is False

    def test_different_domains_tracked_separately(self):
        rl = RateLimiter({"greenhouse.io": 1, "lever.co": 1, "default": 5})
        rl.record("https://boards.greenhouse.io/test/jobs/1")
        # Greenhouse is at limit
        assert rl.can_proceed("https://boards.greenhouse.io/test/jobs/2") is False
        # Lever is still open
        assert rl.can_proceed("https://jobs.lever.co/company/abc") is True

    def test_seconds_until_available_when_available(self):
        rl = RateLimiter({"default": 5})
        assert rl.seconds_until_available("https://example.com") == 0.0

    def test_seconds_until_available_when_at_limit(self):
        rl = RateLimiter({"default": 1})
        rl.record("https://example.com")
        wait = rl.seconds_until_available("https://example.com")
        # Should be roughly 3600 seconds (1 hour)
        assert 3590 < wait <= 3600

    def test_get_status(self):
        rl = RateLimiter({"greenhouse.io": 5, "default": 3})
        rl.record("https://boards.greenhouse.io/a/jobs/1")
        rl.record("https://boards.greenhouse.io/b/jobs/2")

        status = rl.get_status()
        assert "greenhouse.io" in status
        assert status["greenhouse.io"]["used"] == 2
        assert status["greenhouse.io"]["limit"] == 5
        assert status["greenhouse.io"]["available"] == 3

    def test_prune_old_timestamps(self):
        rl = RateLimiter({"default": 1})
        # Manually inject an old timestamp (2 hours ago)
        domain = "example.com"
        rl._timestamps[domain] = [time.time() - 7200]
        # Should be pruned, allowing new request
        assert rl.can_proceed("https://example.com/page") is True

    def test_get_domain_extraction(self):
        rl = RateLimiter({"default": 5})
        assert rl._get_domain("https://boards.greenhouse.io/test") == "greenhouse.io"
        assert rl._get_domain("https://company.wd5.myworkdayjobs.com/jobs") == "myworkdayjobs.com"
        assert rl._get_domain("https://jobs.lever.co/company") == "lever.co"
        assert rl._get_domain("not-a-url") == "unknown"

    def test_record_increments_count(self):
        rl = RateLimiter({"default": 10})
        url = "https://boards.greenhouse.io/test/jobs/1"
        assert rl.can_proceed(url) is True
        rl.record(url)
        rl.record(url)
        rl.record(url)
        status = rl.get_status()
        assert status["greenhouse.io"]["used"] == 3


@pytest.mark.asyncio
async def test_wait_if_needed_no_wait():
    rl = RateLimiter({"default": 5})
    # Should return immediately (no wait needed)
    await rl.wait_if_needed("https://example.com")
