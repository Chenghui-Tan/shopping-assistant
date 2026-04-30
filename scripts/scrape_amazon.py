"""
Amazon scraper — used for "smart display for kitchen" category.
"""
from __future__ import annotations

import asyncio
import urllib.parse

from playwright.async_api import async_playwright

from _browser import (
    SiteBlockedError,
    apply_stealth,
    human_delay,
    is_blocked,
    make_context,
    slow_scroll,
)
from normalize import ScrapedProduct, normalize_delivery, normalize_price, normalize_rating, normalize_review_count

# Keywords to skip — accessories and irrelevant items
SKIP_KEYWORDS = [
    "case", "screen protector", "stand alone", "replacement", "charger",
    "cable", "adapter", "mount bracket", "wall plate", "spare",
]


async def _safe_text(locator, default: str = "") -> str:
    try:
        return (await locator.first.inner_text(timeout=3000)).strip()
    except Exception:
        return default


async def _safe_attr(locator, attr: str, default: str = "") -> str:
    try:
        val = await locator.first.get_attribute(attr, timeout=3000)
        return (val or "").strip()
    except Exception:
        return default


async def _extract_card(card, category: str) -> ScrapedProduct | None:
    try:
        # Title: h2 has class a-text-normal but the *span inside* does not
        title = await _safe_text(card.locator("h2 span").first)
        if not title:
            title = await _safe_text(card.locator("h2 a span"))
        if not title:
            return None

        # Skip accessories
        tl = title.lower()
        if any(kw in tl for kw in SKIP_KEYWORDS):
            return None

        # Product URL via ASIN
        asin = await card.get_attribute("data-asin") or ""
        if asin:
            product_url = f"https://www.amazon.com/dp/{asin}"
        else:
            href = await _safe_attr(card.locator("h2 a.a-link-normal"), "href")
            product_url = f"https://www.amazon.com{href}" if href.startswith("/") else href

        # Price
        price_whole = await _safe_text(card.locator("span.a-price-whole"))
        price_frac = await _safe_text(card.locator("span.a-price-fraction"))
        if price_whole:
            price_raw = f"{price_whole.strip().rstrip('.')}.{price_frac.strip() or '00'}"
            price = normalize_price(price_raw)
        else:
            price = None

        # Rating
        rating_text = await _safe_attr(card.locator("span.a-icon-alt"), "innerHTML")
        if not rating_text:
            rating_text = await _safe_text(card.locator("span.a-icon-alt"))
        rating = normalize_rating(rating_text)

        # Review count — confirmed selector: a.s-underline-link-text (returns "(1K)" etc.)
        rc_text = await _safe_text(card.locator("a.s-underline-link-text"))
        if not rc_text:
            rc_text = await _safe_text(card.locator("span.a-size-base.s-underline-text"))
        review_count = normalize_review_count(rc_text)

        # Image
        image_url = await _safe_attr(card.locator("img.s-image"), "src")

        # Delivery — Amazon uses udm-primary-delivery-message div
        delivery_text = await _safe_text(
            card.locator(".udm-primary-delivery-message")
        )
        if not delivery_text:
            delivery_text = await _safe_text(
                card.locator("span[data-csa-c-delivery-time]")
            )
        if not delivery_text:
            delivery_text = await _safe_text(
                card.locator("div.a-row.a-size-base span.a-color-success")
            )
        arrival_time_days = normalize_delivery(delivery_text)

        # Description (sponsored tag or badge text — actual desc needs PDP visit)
        description = await _safe_text(card.locator("span.a-size-base-plus"))

        return ScrapedProduct(
            category=category,
            source="amazon",
            title=title,
            price=price,
            rating=rating,
            review_count=review_count,
            image_url=image_url or None,
            product_url=product_url,
            description=description or None,
            arrival_time_days=arrival_time_days,
        )
    except Exception:
        return None


async def scrape(
    query: str,
    category: str,
    max_results: int = 30,
    headed: bool = False,
) -> list[ScrapedProduct]:
    encoded = urllib.parse.quote_plus(query)
    url = f"https://www.amazon.com/s?k={encoded}&s=review-rank"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not headed, slow_mo=50)
        context = await make_context(browser)
        page = await context.new_page()
        await apply_stealth(page)

        print(f"  [amazon] Navigating to search: {query}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await human_delay(2, 4)

        if await is_blocked(page):
            await browser.close()
            raise SiteBlockedError("Amazon returned a bot-detection page")

        await slow_scroll(page)
        await human_delay(1, 2)

        cards = page.locator('div[data-component-type="s-search-result"]')
        count = await cards.count()
        print(f"  [amazon] Found {count} product cards")

        if count == 0:
            await browser.close()
            raise SiteBlockedError("Amazon returned zero product cards — likely blocked")

        products: list[ScrapedProduct] = []
        for i in range(min(count, max_results)):
            product = await _extract_card(cards.nth(i), category)
            if product:
                products.append(product)
            if len(products) >= max_results:
                break
            await asyncio.sleep(0.05)

        await browser.close()
        print(f"  [amazon] Extracted {len(products)} products")
        return products


if __name__ == "__main__":
    results = asyncio.run(scrape("smart display kitchen", "smart_display", headed=True))
    for r in results:
        print(r["title"], r["price"], r["rating"])
