"""
Best Buy scraper — fallback for "smart display for kitchen" category.

Confirmed selectors (March 2025):
- Cards:    ul.product-grid-view-container li[data-testid]  (filter: numeric data-testid = real products)
- Title:    h3.product-title inner_text
- URL:      https://www.bestbuy.com/site/-/{skuId}.p  (skuId = numeric data-testid value)
- Price:    [data-testid="price-block-customer-price"] span.sr-only
- Rating:   p.visually-hidden  (text: "Rating 4.5 out of 5 stars with 1234 reviews")
- Image:    img[data-testid="product-image"] src
- Delivery: first text from [class*="delivery"] or [class*="fulfillment"]
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

SKIP_KEYWORDS = [
    "stand for", "stand only", "screen protector", "wall plate",
    "replacement", "cable", "adapter", "charger",
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


def _is_numeric(s: str) -> bool:
    return s.isdigit()


async def _extract_card(card, category: str) -> ScrapedProduct | None:
    try:
        # Only process real product cards (numeric skuId in data-testid)
        sku_id = await card.get_attribute("data-testid") or ""
        if not _is_numeric(sku_id):
            return None

        # Title
        title = await _safe_text(card.locator("h3.product-title"))
        if not title:
            return None

        tl = title.lower()
        if any(kw in tl for kw in SKIP_KEYWORDS):
            return None

        # Product URL from SKU ID
        product_url = f"https://www.bestbuy.com/site/-/{sku_id}.p"

        # Price
        price_text = await _safe_text(
            card.locator('[data-testid="price-block-customer-price"] span.sr-only')
        )
        price = normalize_price(price_text)

        # Rating and review count from accessible text: "Rating 4.5 out of 5 stars with 1234 reviews"
        rating_text = await _safe_text(card.locator("p.visually-hidden"))
        rating = normalize_rating(rating_text)
        review_count = normalize_review_count(rating_text)

        # Image
        image_url = await _safe_attr(card.locator('img[data-testid="product-image"]'), "src")
        if not image_url:
            image_url = await _safe_attr(card.locator("img").first, "src")

        # Delivery
        delivery_text = await _safe_text(card.locator('[class*="delivery"]'))
        if not delivery_text:
            delivery_text = await _safe_text(card.locator('[class*="fulfillment"]'))
        arrival_time_days = normalize_delivery(delivery_text)

        return ScrapedProduct(
            category=category,
            source="bestbuy",
            title=title,
            price=price,
            rating=rating,
            review_count=review_count,
            image_url=image_url or None,
            product_url=product_url,
            description=None,
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
    url = f"https://www.bestbuy.com/site/searchpage.jsp?st={encoded}"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not headed, slow_mo=50)
        context = await make_context(browser)
        page = await context.new_page()
        await apply_stealth(page)

        print(f"  [bestbuy] Navigating to search: {query}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await human_delay(4, 6)

        if await is_blocked(page):
            await browser.close()
            raise SiteBlockedError("Best Buy returned a bot-detection page")

        # Wait for product grid
        try:
            await page.wait_for_selector("#main-results", timeout=15000)
        except Exception:
            await browser.close()
            raise SiteBlockedError("Best Buy main-results did not load")

        # Scroll slowly to trigger lazy loads
        await slow_scroll(page)
        await human_delay(2, 3)

        cards = page.locator("ul.product-grid-view-container li[data-testid]")
        count = await cards.count()
        print(f"  [bestbuy] Found {count} product list items")

        if count == 0:
            await browser.close()
            raise SiteBlockedError("Best Buy returned zero product cards")

        products: list[ScrapedProduct] = []
        for i in range(min(count, max_results * 2)):  # iterate more since some cards get filtered
            product = await _extract_card(cards.nth(i), category)
            if product:
                products.append(product)
            if len(products) >= max_results:
                break
            await asyncio.sleep(0.05)

        await browser.close()
        print(f"  [bestbuy] Extracted {len(products)} products")
        return products


if __name__ == "__main__":
    results = asyncio.run(scrape("smart display echo show", "smart_display", headed=True))
    for r in results:
        print(r["title"], r["price"], r["rating"])
