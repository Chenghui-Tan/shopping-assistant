"""
Target scraper — primary for "water bottle" and "kitchen organizer" categories.

Confirmed selectors (March 2025):
- Cards:    [data-test="@web/site-top-of-funnel/ProductCardWrapper"]
- Title:    img[loading="lazy"] alt attribute
- Price:    [data-test="current-price"] inner_text
- Rating:   [class*="ratingsAndReviews"] span[aria-hidden="true"] inner_text (bare float like "4.7")
- Reviews:  [class*="ratingCount"] inner_text  (e.g. "(16798)")
- URL:      a[href*="/p/"] href attribute (prepend https://www.target.com)
- Image:    img[loading="lazy"] src attribute
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
    "water_bottle": ["replacement lid", "replacement cap", "straw replacement", "cleaning brush"],
    "kitchen_organizer": ["tablecloth", "contact paper"],
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
        # Title from image alt attribute
        title = await _safe_attr(card.locator('img[loading="lazy"]'), "alt")
        if not title:
            return None

        tl = title.lower()
        skip_list = SKIP_KEYWORDS.get(category, [])
        if any(kw in tl for kw in skip_list):
            return None

        # Product URL
        href = await _safe_attr(card.locator('a[href*="/p/"]'), "href")
        product_url = f"https://www.target.com{href}" if href.startswith("/") else href

        # Price
        price_text = await _safe_text(card.locator('[data-test="current-price"]'))
        price = normalize_price(price_text)

        # Rating — bare float like "4.7"
        rating_text = await _safe_text(
            card.locator('[class*="ratingsAndReviews"] span[aria-hidden="true"]')
        )
        rating = normalize_rating(rating_text) if rating_text else None

        # Review count — "(16798)"
        rc_text = await _safe_text(card.locator('[class*="ratingCount"]'))
        review_count = normalize_review_count(rc_text)

        # Image
        image_url = await _safe_attr(card.locator('img[loading="lazy"]'), "src")

        # Delivery — Target shows "Get it by [date]" in fulfillment section
        delivery_text = await _safe_text(card.locator('[data-test="fulfillment-cell"]'))
        if not delivery_text:
            delivery_text = await _safe_text(card.locator('[class*="fulfillment"]'))
        arrival_time_days = normalize_delivery(delivery_text)

        return ScrapedProduct(
            category=category,
            source="target",
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
    url = f"https://www.target.com/s?searchTerm={encoded}&sortBy=bestselling"

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=not headed, slow_mo=50)
        context = await make_context(browser)
        page = await context.new_page()
        await apply_stealth(page)

        print(f"  [target] Navigating to search: {query}")
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await human_delay(3, 5)

        if await is_blocked(page):
            await browser.close()
            raise SiteBlockedError("Target returned a bot-detection page")

        # Wait for product grid (Target is CSR)
        try:
            await page.wait_for_selector(
                '[data-test="@web/site-top-of-funnel/ProductCardWrapper"]',
                timeout=20000,
            )
        except Exception:
            await browser.close()
            raise SiteBlockedError("Target product grid did not load")

        # Scroll twice to load lazy images
        await slow_scroll(page)
        await asyncio.sleep(1)
        await slow_scroll(page)
        await human_delay(0.5, 1.5)

        cards = page.locator('[data-test="@web/site-top-of-funnel/ProductCardWrapper"]')
        count = await cards.count()
        print(f"  [target] Found {count} product cards")

        if count == 0:
            await browser.close()
            raise SiteBlockedError("Target returned zero product cards")

        products: list[ScrapedProduct] = []
        for i in range(min(count, max_results)):
            product = await _extract_card(cards.nth(i), category)
            if product:
                products.append(product)
            if len(products) >= max_results:
                break
            await asyncio.sleep(0.05)

        # If we need more and got a full first page (~24), fetch page 2
        if len(products) < max_results and count >= 24:
            url2 = url + "&Nao=24"
            print(f"  [target] Fetching page 2")
            try:
                await page.goto(url2, wait_until="domcontentloaded", timeout=30000)
                await human_delay(2, 3)
                await page.wait_for_selector(
                    '[data-test="@web/site-top-of-funnel/ProductCardWrapper"]',
                    timeout=15000,
                )
                await slow_scroll(page)
                cards2 = page.locator('[data-test="@web/site-top-of-funnel/ProductCardWrapper"]')
                count2 = await cards2.count()
                needed = max_results - len(products)
                for i in range(min(count2, needed)):
                    product = await _extract_card(cards2.nth(i), category)
                    if product:
                        products.append(product)
                    if len(products) >= max_results:
                        break
            except Exception:
                pass

        await browser.close()
        print(f"  [target] Extracted {len(products)} products")
        return products


if __name__ == "__main__":
    results = asyncio.run(scrape("insulated water bottle", "water_bottle", headed=True))
    for r in results:
        print(r["title"], r["price"], r["rating"])
