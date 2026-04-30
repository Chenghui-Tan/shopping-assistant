"""
Scraping pipeline orchestrator.

Usage:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --headed
    python scripts/run_pipeline.py --category water_bottle
    python scripts/run_pipeline.py --category smart_display --headed
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
from collections import Counter
from pathlib import Path

# Allow importing sibling scripts directly
sys.path.insert(0, str(Path(__file__).parent))

import scrape_amazon
import scrape_bestbuy
import scrape_walmart
import scrape_target
from _browser import InsufficientResultsError, SiteBlockedError
from normalize import ScrapedProduct, clean_and_combine, deduplicate

ROOT = Path(__file__).parent.parent
RAW_DIR = ROOT / "data" / "raw"
CLEAN_DIR = ROOT / "data" / "clean"

# Pipeline configuration:
#   (category, primary_mod, fallback_mod, queries, filename)
#   queries: list of (mod, query) pairs tried in order, stopping at first success.
#   Supplemental queries run after primary success to boost count toward TARGET_PER_CATEGORY.
#
# Note: Walmart blocks reliably — Target is primary for water/kitchen.
#       Amazon primary for smart_display; Best Buy is fallback.
TARGET_PER_CATEGORY = 25

PIPELINE = [
    {
        "category": "smart_display",
        "filename": "smart_display.json",
        "primary": (scrape_amazon, "smart display for kitchen"),
        "fallback": (scrape_bestbuy, "smart display echo show google nest hub"),
        "supplement": [
            (scrape_amazon, "echo show smart home display kitchen"),
            (scrape_bestbuy, "google nest hub echo show smart display"),
        ],
    },
    {
        "category": "water_bottle",
        "filename": "water_bottle.json",
        "primary": (scrape_target, "insulated water bottle"),
        "fallback": (scrape_walmart, "insulated water bottle"),
        "supplement": [
            (scrape_target, "hydroflask stanley tumbler insulated bottle"),
            (scrape_target, "vacuum insulated water bottle 32oz"),
        ],
    },
    {
        "category": "kitchen_organizer",
        "filename": "kitchen_organizer.json",
        "primary": (scrape_target, "kitchen drawer organizer"),
        "fallback": (scrape_walmart, "kitchen drawer organizer"),
        "supplement": [
            (scrape_target, "cabinet shelf organizer kitchen"),
            (scrape_target, "pantry organizer bins kitchen storage"),
        ],
    },
]

FALLBACK_LOG: list[str] = []


async def scrape_with_fallback(
    cfg: dict, headed: bool
) -> list[ScrapedProduct]:
    """Try primary then fallback scraper; return results from first success."""
    category = cfg["category"]
    primary_mod, primary_q = cfg["primary"]
    fallback_mod, fallback_q = cfg["fallback"]

    for attempt, (mod, query, label) in enumerate([
        (primary_mod, primary_q, "primary"),
        (fallback_mod, fallback_q, "fallback"),
    ]):
        try:
            results = await mod.scrape(
                query=query,
                category=category,
                max_results=TARGET_PER_CATEGORY + 10,
                headed=headed,
            )
            if len(results) < 5:
                raise InsufficientResultsError(f"Only {len(results)} products returned")
            source = results[0]["source"] if results else mod.__name__
            print(f"  [{category}] {label} ({source}) succeeded: {len(results)} products")
            if attempt == 1:
                FALLBACK_LOG.append(f"{category}: used fallback ({source}) — primary failed")
            return results

        except (SiteBlockedError, InsufficientResultsError, Exception) as e:
            print(f"  [{category}] {label} failed: {type(e).__name__}: {e}")
            if attempt == 0:
                wait = random.uniform(4, 8)
                print(f"  [{category}] Waiting {wait:.1f}s before trying fallback...")
                await asyncio.sleep(wait)
            else:
                print(f"  [{category}] Both scrapers failed — skipping category")
                FALLBACK_LOG.append(f"{category}: BOTH scrapers failed — no data")
                return []

    return []


async def boost_with_supplements(
    products: list[ScrapedProduct],
    cfg: dict,
    headed: bool,
) -> list[ScrapedProduct]:
    """Run supplemental queries if below TARGET_PER_CATEGORY after dedup."""
    category = cfg["category"]
    combined = list(products)

    for mod, query in cfg.get("supplement", []):
        current_unique = len(deduplicate(combined))
        if current_unique >= TARGET_PER_CATEGORY:
            break
        needed = TARGET_PER_CATEGORY - current_unique + 5  # fetch a few extra
        print(f"  [{category}] Supplemental scrape ({mod.__name__.replace('scrape_', '')}, need {needed} more): {query}")
        wait = random.uniform(3, 6)
        print(f"  [{category}] Waiting {wait:.1f}s...")
        await asyncio.sleep(wait)
        try:
            extra = await mod.scrape(
                query=query,
                category=category,
                max_results=needed + 10,
                headed=headed,
            )
            combined.extend(extra)
            print(f"  [{category}] +{len(extra)} supplemental → {len(deduplicate(combined))} unique so far")
        except Exception as e:
            print(f"  [{category}] Supplemental failed: {e}")

    return combined


async def run(categories: list[str], headed: bool) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    all_raw: list[list[ScrapedProduct]] = []

    for i, cfg in enumerate(PIPELINE):
        cat = cfg["category"]

        if categories and cat not in categories:
            continue

        print(f"\n{'='*50}")
        print(f"Scraping: {cat}")
        print(f"{'='*50}")

        products = await scrape_with_fallback(cfg, headed)

        if products:
            # Boost count with supplemental queries if needed
            products = await boost_with_supplements(products, cfg, headed)

            out_path = RAW_DIR / cfg["filename"]
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            unique_count = len(deduplicate(products))
            print(f"  Saved {len(products)} raw products ({unique_count} unique) → {out_path.relative_to(ROOT)}")
            all_raw.append(products)

        # Pause between categories
        if i < len(PIPELINE) - 1:
            wait = random.uniform(5, 10)
            print(f"\n  Waiting {wait:.1f}s before next category...")
            await asyncio.sleep(wait)

    # Combine and clean all data
    if all_raw:
        print(f"\n{'='*50}")
        print("Combining and cleaning all data...")
        cleaned = clean_and_combine(all_raw)
        clean_path = CLEAN_DIR / "products_clean.json"
        with open(clean_path, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, indent=2, ensure_ascii=False)
        print(f"  Saved {len(cleaned)} cleaned products → {clean_path.relative_to(ROOT)}")

        print(f"\n{'='*50}")
        print("PIPELINE SUMMARY")
        print(f"{'='*50}")
        by_category = Counter(p["category"] for p in cleaned)
        by_source = Counter(p["source"] for p in cleaned)
        for cat, count in sorted(by_category.items()):
            print(f"  {cat}: {count} products")
        print()
        for source, count in sorted(by_source.items()):
            print(f"  source={source}: {count} products")
        if FALLBACK_LOG:
            print("\nFallback events:")
            for msg in FALLBACK_LOG:
                print(f"  ! {msg}")
        print(f"\nTotal: {len(cleaned)} products in data/clean/products_clean.json")
    else:
        print("\nNo products scraped — check errors above.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the shopping assistant scraping pipeline")
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in headed (visible) mode — helps bypass bot detection",
    )
    parser.add_argument(
        "--category",
        choices=["smart_display", "water_bottle", "kitchen_organizer"],
        help="Scrape only one category (default: all)",
    )
    args = parser.parse_args()

    categories = [args.category] if args.category else []
    asyncio.run(run(categories=categories, headed=args.headed))


if __name__ == "__main__":
    main()
