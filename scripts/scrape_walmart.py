"""
Walmart scraper — used for "water bottle" and "kitchen organizer" categories.
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

SKIP_KEYWORDS = {
    "water_bottle": ["replacement lid", "replacement cap", "straw replacement", "cleaning brush", "carrying bag"],
    "kitchen_organizer": ["tablecloth", "shelf liner only", "contact paper"],
}


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
        # Title
        title = await _safe_text(card.locator('[data-automation-id="product-title"]'))
        if not title:
            title = await _safe_text(card.locator("span[class*='normal']"))
        if not title:
            return None

        tl = title.lower()
        skip_list = SKIP_KEYWORDS.get(category, [])
        if any(kw in tl for kw in skip_list):
            return None

        # Product URL
        href = await _safe_attr(card.locator("a[link-identifier]"), "href")
        if not href:
            href = await _safe_attr(card.locator("a[class*='product']"), "href")
        if not href:
            href = await _safe_attr(card.locator("a").first, "href")
        product_url = f"https://www.walmart.com{href}" if href.startswith("/") else href

        # Price — prefer itemprop content attribute (clean float)
        price_content = await _safe_attr(
            card.locator('[itemprop="price"]'), "content"
        )
        if price_content:
            try:
                price = float(price_content)
            except ValueError:
                price = normalize_price(price_content)
        else:
            price_text = await _safe_text(card.locator('[data-testid="price-wrap"]'))
            if not price_text:
                price_text = await _safe_text(card.locator("[class*='price']"))
            price = normalize_price(price_text)

        # Rating
        rating_label = await _safe_attr(
            card.locator("[aria-label*='stars']"), "aria-label"
        )
        if not rating_label:
            rating_label = await _safe_attr(
                card.locator("[aria-label*='out of 5']"), "aria-label"
            )
        rating = normalize_rating(rating_label)

        # Review count
        rc_label = await _safe_attr(
            card.locator("[aria-label*='rating']"), "aria-label"
        )
        review_count = normalize_review_count(rc_label)

        # Image
        image_url = await _safe_attr(card.locator('img[data-testid="productTileImage"]'), "src")
        if not image_url:
            image_url = await _safe_attr(card.locator("img").first, "src")

        # Delivery
        delivery_text = await _safe_text(
            card.locator('[data-testid="fulfillment-badge"]')
        )
        if not delivery_text:
            delivery_text = await _safe_text(
                card.locator('[data-testid="arrival-date"]')
            )
        if not delivery_text:
            delivery_text = await _safe_text(
                card.locator("[class*='fulfillment']")
            )
        arrival_time_days = normalize_delivery(delivery_text)

        return ScrapedProduct(
            category=category,
            source="walmart",
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
    url = f"https://www.walmart.com/search?q={encoded}&sort=best_seller"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not headed, slow_mo=50)
        context = await make_context(browser)
        page = await context.new_page()
        await apply_stealth(page)

        print(f"  [walmart] Navigating to search: {query}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await human_delay(2, 4)

        if await is_blocked(page):
            await browser.close()
            raise SiteBlockedError("Walmart returned a bot-detection page")

        # Wait for product grid to hydrate
        try:
            await page.wait_for_selector("div[data-item-id]", timeout=20000)
        except Exception:
            # Try alternate selector
            try:
                await page.wait_for_selector('[data-testid="list-view"]', timeout=10000)
            except Exception:
                await browser.close()
                raise SiteBlockedError("Walmart product grid did not load")

        await slow_scroll(page)
        # Extra wait for lazy delivery badges
        await page.wait_for_timeout(2000)
        await human_delay(0.5, 1.5)

        cards = page.locator("div[data-item-id]")
        count = await cards.count()
        print(f"  [walmart] Found {count} product cards")

        if count == 0:
            await browser.close()
            raise SiteBlockedError("Walmart returned zero product cards")

        products: list[ScrapedProduct] = []
        for i in range(min(count, max_results)):
            product = await _extract_card(cards.nth(i), category)
            if product:
                products.append(product)
            if len(products) >= max_results:
                break
            await asyncio.sleep(0.05)

        await browser.close()
        print(f"  [walmart] Extracted {len(products)} products")
        return products


if __name__ == "__main__":
    results = asyncio.run(scrape("insulated water bottle", "water_bottle", headed=True))
    for r in results:
        print(r["title"], r["price"], r["rating"])
