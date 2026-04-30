"""
Shared data types and normalization utilities for the scraping pipeline.
"""
from __future__ import annotations

import re
import unicodedata
from datetime import date
from typing import TypedDict


MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4,
    "may": 5, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


class ScrapedProduct(TypedDict):
    category: str           # "smart_display" | "water_bottle" | "kitchen_organizer"
    source: str             # "amazon" | "bestbuy" | "walmart" | "target"
    title: str
    price: float | None
    rating: float | None
    review_count: int | None
    image_url: str | None
    product_url: str
    description: str | None
    arrival_time_days: int | None


def normalize_price(raw: str | None) -> float | None:
    if not raw:
        return None
    # Take the first price in a range like "$12.99 - $24.99"
    cleaned = raw.replace(",", "")
    m = re.search(r"\$?([\d]+\.?\d*)", cleaned)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def normalize_rating(raw: str | None) -> float | None:
    if not raw:
        return None
    m = re.search(r"([\d]+\.?\d*)\s*(?:out of|/)\s*5", raw, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    # bare float like "4.5"
    m = re.search(r"([\d]\.\d)", raw)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    return None


def normalize_review_count(raw: str | None) -> int | None:
    if not raw:
        return None
    # Handle "Rating X out of 5 stars with N reviews" (Best Buy format)
    m = re.search(r"with\s+([\d,]+)\s+review", raw, re.IGNORECASE)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except ValueError:
            pass
    # Handle "1K", "2.5K", "1M" shorthand (Amazon format)
    m = re.search(r"([\d,.]+)\s*([KkMm])", raw)
    if m:
        num = float(m.group(1).replace(",", ""))
        suffix = m.group(2).upper()
        multiplier = 1000 if suffix == "K" else 1_000_000
        return int(num * multiplier)
    # Plain number with possible commas and parens: "(12,345)" or "12345"
    cleaned = re.sub(r"[,()\s]", "", raw)
    m = re.search(r"(\d+)", cleaned)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return None


def normalize_delivery(raw: str | None) -> int | None:
    """Convert delivery text to number of days from today."""
    if not raw:
        return None
    s = raw.lower().strip()

    if "today" in s or "same day" in s or "same-day" in s:
        return 0
    if "tomorrow" in s:
        return 1

    # "in N days" / "N-day shipping" / "N day"
    m = re.search(r"in\s+(\d+)\s+day", s)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)-day", s)
    if m:
        return int(m.group(1))
    m = re.search(r"(\d+)\s+day", s)
    if m:
        return int(m.group(1))

    # "2-3 days" range — take lower bound
    m = re.search(r"(\d+)\s*[-–]\s*\d+\s+day", s)
    if m:
        return int(m.group(1))

    # Absolute date: "by Mon, Mar 14" / "arrives Mar 14" / "get it by Mar 14"
    m = re.search(
        r"(?:by|arrives?|get it by)[^a-z]*([a-z]{3})\w*\s*[,.]?\s*(\d{1,2})", s
    )
    if m:
        result = _days_until_month_day(m.group(1), m.group(2))
        if result is not None:
            return result

    # "Month D-D" range — take lower bound
    m = re.search(r"([a-z]{3})\w*\s+(\d{1,2})\s*[-–]\s*\d{1,2}", s)
    if m:
        result = _days_until_month_day(m.group(1), m.group(2))
        if result is not None:
            return result

    # Standalone "Month D"
    m = re.search(r"([a-z]{3})\w*\s+(\d{1,2})", s)
    if m:
        result = _days_until_month_day(m.group(1), m.group(2))
        if result is not None:
            return result

    return None


def _days_until_month_day(month_str: str, day_str: str | int) -> int | None:
    month_num = MONTHS.get(month_str[:3].lower())
    if not month_num:
        return None
    try:
        day = int(day_str)
        today = date.today()
        year = today.year if month_num >= today.month else today.year + 1
        target = date(year, month_num, day)
        return max(0, (target - today).days)
    except (ValueError, OverflowError):
        return None


def _title_key(title: str) -> str:
    """Normalize a title for fuzzy deduplication."""
    t = unicodedata.normalize("NFKD", title.lower())
    return re.sub(r"[^a-z0-9 ]", "", t).strip()


def deduplicate(products: list[ScrapedProduct]) -> list[ScrapedProduct]:
    """Remove exact URL duplicates, then fuzzy-deduplicate by title."""
    # Phase 1: exact URL dedup
    seen_urls: dict[str, ScrapedProduct] = {}
    for p in products:
        key = p["product_url"].rstrip("/")
        if key not in seen_urls:
            seen_urls[key] = p

    unique = list(seen_urls.values())

    # Phase 2: fuzzy title dedup within the same category
    #   If two products have the same normalized title prefix (first 65 chars),
    #   keep the one with higher review_count. 65 chars preserves color/size variants
    #   while still collapsing true duplicates from different pages.
    title_map: dict[str, ScrapedProduct] = {}
    for p in unique:
        tk = _title_key(p["title"])[:65]
        cat_key = f"{p['category']}::{tk}"
        if cat_key not in title_map:
            title_map[cat_key] = p
        else:
            existing = title_map[cat_key]
            if (p.get("review_count") or 0) > (existing.get("review_count") or 0):
                title_map[cat_key] = p

    return list(title_map.values())


def clean_and_combine(raw_lists: list[list[ScrapedProduct]]) -> list[ScrapedProduct]:
    """Combine multiple raw lists, normalize all fields, deduplicate, and sort."""
    all_products: list[ScrapedProduct] = []
    for products in raw_lists:
        for p in products:
            p["price"] = normalize_price(str(p.get("price") or "")) if not isinstance(p.get("price"), float) else p["price"]
            p["rating"] = normalize_rating(str(p.get("rating") or "")) if not isinstance(p.get("rating"), float) else p["rating"]
            if not isinstance(p.get("review_count"), int):
                p["review_count"] = normalize_review_count(str(p.get("review_count") or ""))
            if not isinstance(p.get("arrival_time_days"), int):
                p["arrival_time_days"] = normalize_delivery(str(p.get("arrival_time_days") or ""))
            all_products.append(p)

    deduped = deduplicate(all_products)
    deduped.sort(key=lambda p: (p["category"], -(p.get("rating") or 0)))
    return deduped
