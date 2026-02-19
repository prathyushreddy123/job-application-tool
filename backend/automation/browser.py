import asyncio
import logging
import random
from pathlib import Path

from playwright.async_api import BrowserContext, Page, async_playwright

from backend.config import Settings

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages the Playwright browser lifecycle with persistent sessions.

    Uses a persistent browser context (user_data_dir) so login cookies
    and sessions survive across restarts.
    """

    def __init__(self, settings: Settings):
        self._settings = settings
        self._playwright = None
        self._browser = None
        self._context: BrowserContext | None = None
        self._pages: list[Page] = []

    async def start(self):
        """Launch Playwright with a persistent Chromium browser context."""
        profile_dir = Path(self._settings.browser_profile_dir)
        profile_dir.mkdir(parents=True, exist_ok=True)

        self._playwright = await async_playwright().start()
        self._context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=self._settings.headless,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"],
        )
        logger.info(
            f"Browser started (headless={self._settings.headless}, "
            f"profile={profile_dir})"
        )

    async def new_page(self) -> Page:
        """Create and return a new browser page/tab."""
        if self._context is None:
            raise RuntimeError("Browser not started. Call start() first.")
        page = await self._context.new_page()
        self._pages.append(page)
        return page

    async def close_page(self, page: Page):
        """Close a specific browser page."""
        if page in self._pages:
            self._pages.remove(page)
        try:
            await page.close()
        except Exception:
            pass

    async def screenshot(self, page: Page, path: str) -> str:
        """Take a full-page screenshot and save to path."""
        screenshot_path = Path(path)
        screenshot_path.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(screenshot_path), full_page=True)
        logger.info(f"Screenshot saved: {screenshot_path}")
        return str(screenshot_path)

    async def bring_to_front(self, page: Page):
        """Bring the browser page to the foreground (for CAPTCHA/edit mode)."""
        try:
            await page.bring_to_front()
        except Exception as e:
            logger.warning(f"Could not bring page to front: {e}")

    async def random_delay(self):
        """Sleep for a random duration between configured min/max delays."""
        delay_ms = random.randint(
            self._settings.delay_min_ms,
            self._settings.delay_max_ms,
        )
        await asyncio.sleep(delay_ms / 1000.0)

    async def stop(self):
        """Close all pages and shut down the browser."""
        for page in list(self._pages):
            await self.close_page(page)
        self._pages.clear()

        if self._context is not None:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None

        if self._playwright is not None:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None

        logger.info("Browser stopped")

    @property
    def is_running(self) -> bool:
        return self._context is not None

    @property
    def open_pages(self) -> int:
        return len(self._pages)
