"""Tests for backend/config.py"""
import json

from backend.config import Settings


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.api_key == "dev-key"
        assert s.fastapi_port == 8000
        assert s.fill_ahead_buffer == 3
        assert s.demo is False
        assert s.dry_run is False
        assert s.headless is False

    def test_rate_limits_parsing(self):
        s = Settings()
        limits = s.get_rate_limits()
        assert isinstance(limits, dict)
        assert "greenhouse.io" in limits
        assert limits["default"] == 5

    def test_custom_rate_limits(self):
        s = Settings(rate_limits='{"example.com": 10, "default": 3}')
        limits = s.get_rate_limits()
        assert limits["example.com"] == 10
        assert limits["default"] == 3

    def test_data_dir_is_path(self):
        s = Settings()
        from pathlib import Path
        assert isinstance(s.data_dir, Path)
        assert isinstance(s.browser_profile_dir, Path)

    def test_gemini_key_default_empty(self):
        s = Settings()
        assert s.gemini_api_key == ""
