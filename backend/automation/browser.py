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

    async def detect_login_wall(self, page: Page) -> bool:
        """Check if the page is a login/SSO wall instead of a job application."""
        # Check URL patterns that indicate login redirects
        url = page.url.lower()
        login_url_patterns = [
            "/login", "/signin", "/sign-in", "/sso",
            "/auth", "/authenticate", "/oauth",
            "accounts.google.com", "login.microsoftonline.com",
            "sso.", "/saml", "/cas/login",
        ]
        for pattern in login_url_patterns:
            if pattern in url:
                logger.warning(f"Login wall detected (URL): {page.url}")
                return True

        # Check for login form elements on the page
        try:
            login_markers = await page.query_selector(
                'input[type="password"], '
                'form[action*="login"], '
                'form[action*="signin"], '
                'form[action*="auth"], '
                'button:has-text("Log in"), '
                'button:has-text("Sign in")'
            )
            if login_markers is not None:
                # Double-check: if there's also a resume upload or job-related
                # element, it's probably an application form, not a login wall
                job_marker = await page.query_selector(
                    'input[type="file"], '
                    'input[name*="resume"], '
                    'textarea[name*="cover"], '
                    '#application-form, '
                    '[data-automation-id="applicationContent"]'
                )
                if job_marker is None:
                    logger.warning("Login wall detected (form elements)")
                    return True
        except Exception:
            pass

        return False

    async def detect_captcha(self, page: Page) -> bool:
        """Check if the page contains a CAPTCHA that needs manual solving."""
        captcha_selectors = [
            'iframe[src*="recaptcha"]',
            'iframe[src*="hcaptcha"]',
            '.g-recaptcha',
            '#captcha',
            '[data-captcha]',
            'iframe[src*="challenge"]',
            '.h-captcha',
            '#cf-challenge-running',  # Cloudflare challenge
        ]
        try:
            for selector in captcha_selectors:
                element = await page.query_selector(selector)
                if element is not None:
                    logger.warning(f"CAPTCHA detected: {selector}")
                    return True
        except Exception:
            pass
        return False

    async def detect_validation_errors(self, page: Page) -> list[str]:
        """Scan the page for visible form validation error messages.

        Returns a list of error message strings found on the page.
        """
        errors: list[str] = []
        error_selectors = [
            '.error-message',
            '.field-error',
            '.validation-error',
            '.form-error',
            '[role="alert"]',
            '.invalid-feedback',
            '.help-block.error',
            '.text-danger',
            '[data-automation-id="errorMessage"]',  # Workday
            '.error',
        ]
        try:
            for selector in error_selectors:
                elements = await page.query_selector_all(selector)
                for el in elements:
                    visible = await el.is_visible()
                    if not visible:
                        continue
                    text = (await el.inner_text()).strip()
                    if text and len(text) > 3 and text not in errors:
                        errors.append(text)
        except Exception:
            pass

        # Also check for inputs with aria-invalid="true"
        try:
            invalid_inputs = await page.query_selector_all(
                'input[aria-invalid="true"], '
                'textarea[aria-invalid="true"], '
                'select[aria-invalid="true"]'
            )
            for inp in invalid_inputs:
                name = await inp.get_attribute("name") or ""
                aria_desc = await inp.get_attribute("aria-describedby") or ""
                label = name or aria_desc or "unknown field"
                msg = f"Validation error on: {label}"
                if msg not in errors:
                    errors.append(msg)
        except Exception:
            pass

        if errors:
            logger.warning(f"Found {len(errors)} validation error(s) on page")
        return errors

    @property
    def is_running(self) -> bool:
        return self._context is not None

    @property
    def open_pages(self) -> int:
        return len(self._pages)
