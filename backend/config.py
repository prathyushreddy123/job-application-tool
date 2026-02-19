import json
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # FastAPI
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000
    api_key: str = "dev-key"

    # n8n
    n8n_url: str = "http://localhost:5678"
    n8n_webhook_url: str = "http://localhost:5678/webhook"

    # Data
    data_dir: Path = Path("./data")
    browser_profile_dir: Path = Path("./data/browser-profile")

    # Automation
    delay_min_ms: int = 150
    delay_max_ms: int = 750
    fill_ahead_buffer: int = 3
    headless: bool = False
    dry_run: bool = False
    demo: bool = False

    # Rate limits (JSON string)
    rate_limits: str = '{"greenhouse.io": 5, "default": 5}'

    # Gemini
    gemini_api_key: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def get_rate_limits(self) -> dict:
        return json.loads(self.rate_limits)


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
