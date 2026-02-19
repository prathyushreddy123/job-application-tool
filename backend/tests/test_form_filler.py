from unittest.mock import MagicMock

from backend.automation.form_filler import FormFillingPipeline
from backend.automation.rate_limiter import RateLimiter
from backend.config import Settings


def test_pipeline_initial_status():
    """Pipeline should report correct initial status without starting."""
    settings = Settings(data_dir="./data")
    rate_limiter = RateLimiter({"default": 5})
    browser = MagicMock()

    pipeline = FormFillingPipeline(browser, settings, rate_limiter)
    status = pipeline.status

    assert status["running"] is False
    assert status["pending_count"] == 0
    assert status["ready_count"] == 0
    assert status["total_processed"] == 0
    assert status["consecutive_failures"] == 0


def test_pipeline_is_queue_empty():
    settings = Settings(data_dir="./data")
    rate_limiter = RateLimiter({"default": 5})
    browser = MagicMock()

    pipeline = FormFillingPipeline(browser, settings, rate_limiter)
    assert pipeline.is_queue_empty is True
