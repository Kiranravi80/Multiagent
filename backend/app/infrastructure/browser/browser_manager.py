"""Playwright Browser Manager.

Provides thread-safe access to a pooled browser instance with anti-detection headers.
"""

from __future__ import annotations

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from app.core.logging import get_logger

logger = get_logger(__name__)


class BrowserManager:
    """Manages the Playwright browser lifecycle and page contexts."""

    def __init__(self, headless: bool = True, timeout_ms: int = 30000) -> None:
        self._headless = headless
        self._timeout_ms = timeout_ms
        self._playwright: Any = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    async def start(self) -> None:
        """Launch the browser instance with anti-fingerprint evasion arguments."""
        if self._browser:
            return

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self._headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-infobars",
                "--window-size=1920,1080",
            ],
        )

        # Standard user-agent and window configurations
        self._context = await self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        self._context.set_default_timeout(self._timeout_ms)
        logger.info("browser_manager_started", headless=self._headless)

    async def stop(self) -> None:
        """Gracefully close browser contexts."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("browser_manager_stopped")

    async def get_page(self) -> Page:
        """Create a new page session."""
        if not self._context:
            await self.start()
        assert self._context is not None
        page = await self._context.new_page()

        # Evade basic automation detection mechanisms
        await page.add_init_script(
            "const newProto = Navigator.prototype;"
            "delete newProto.webdriver;"
        )
        return page

    async def close_page(self, page: Page) -> None:
        """Safely close an active page."""
        await page.close()
