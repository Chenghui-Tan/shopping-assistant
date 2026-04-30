"""
Shared browser helpers for all scrapers.
"""
from __future__ import annotations

import asyncio
import random

from playwright.async_api import Browser, BrowserContext, Page


HEADLESS_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

BLOCKED_SIGNALS = [
    "robot", "captcha", "challenge", "verify", "access denied",
    "automated", "unusual traffic", "cf-challenge", "just a moment",
    "are you human", "bot detection",
]


class SiteBlockedError(Exception):
    pass


class InsufficientResultsError(Exception):
    pass


async def make_context(browser: Browser) -> BrowserContext:
    context = await browser.new_context(
        user_agent=HEADLESS_UA,
        viewport={"width": 1440, "height": 900},
        locale="en-US",
        timezone_id="America/Chicago",
        color_scheme="light",
        java_script_enabled=True,
        extra_http_headers={
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        },
    )
    await context.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
        Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});
        window.chrome = {runtime: {}};
    """)
    return context


async def apply_stealth(page: Page) -> None:
    try:
        from playwright_stealth import Stealth
        await Stealth().apply_stealth_async(page)
    except Exception:
        pass  # stealth is best-effort


async def is_blocked(page: Page) -> bool:
    try:
        title = (await page.title()).lower()
        url = page.url.lower()
        return any(s in title or s in url for s in BLOCKED_SIGNALS)
    except Exception:
        return False


async def human_delay(low: float = 1.5, high: float = 3.5) -> None:
    await asyncio.sleep(random.uniform(low, high))


async def slow_scroll(page: Page, steps: int = 8, max_y: int = 4000) -> None:
    step_size = max_y // steps
    for i in range(steps):
        await page.evaluate(f"window.scrollTo(0, {step_size * (i + 1)})")
        await asyncio.sleep(random.uniform(0.2, 0.5))
    # scroll back to top so lazy-load images finish
    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(0.5)
