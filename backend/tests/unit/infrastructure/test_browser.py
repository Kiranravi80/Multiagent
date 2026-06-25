import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.infrastructure.browser.browser_manager import BrowserManager


@pytest.mark.asyncio
async def test_browser_manager_lifecycle() -> None:
    """Test Playwright browser manager boot and page orchestration lifecycle."""
    with patch("app.infrastructure.browser.browser_manager.async_playwright") as mock_ap:
        mock_playwright_instance = AsyncMock()
        mock_browser = AsyncMock()
        mock_context = MagicMock()
        mock_context.close = AsyncMock()
        mock_context.new_page = AsyncMock()

        mock_ap.return_value.start = AsyncMock(return_value=mock_playwright_instance)
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
        mock_browser.new_context = AsyncMock(return_value=mock_context)

        manager = BrowserManager(headless=True)
        await manager.start()

        assert manager._browser is not None

        # Mock page creation
        mock_page = AsyncMock()
        mock_context.new_page.return_value = mock_page

        page = await manager.get_page()
        assert page is not None
        mock_context.new_page.assert_called_once()

        await manager.close_page(page)
        mock_page.close.assert_called_once()

        await manager.stop()
        mock_browser.close.assert_called_once()
        mock_playwright_instance.stop.assert_called_once()
