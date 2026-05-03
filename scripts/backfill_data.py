"""
Backfill missing fields in data/clean/products_clean.json.

Honest about what's synthesized:
  - Each backfilled field gets a sibling `*_source` flag of "scraped" or
    "estimated" so anyone reading the data downstream knows which is which.
  - Estimates are deterministic (seeded by product_url hash) so reruns
    don't perturb ranking results.
  - Original verified values are never overwritten.

Fields touched:
  description           — synthesized from title + category for every product.
                          Improves engine.infer_features (which reads
                          description) and gives Claude more context.
  arrival_time_days     — backfilled for Target products only (Amazon already
                          has 28/30). Target standard ground delivery is
                          2–4 business days; we sample deterministically
                          in [2, 4].
  rating, review_count  — backfilled to the category median when missing.
"""
from __future__ import annotations

import hashlib
import json
import statistics
from pathlib import Path

DATA_PATH = Path(__file__).parent.parent / "data" / "clean" / "products_clean.json"


# ----------------------------------------------------------------------------
# Description synthesis. Template-based — never invents specs not in the title;
# only restates what the title already says, plus a category-suitable
# closing line. This is purely to give the engine more keyword surface for
# feature inference and to give Claude richer context.
# ----------------------------------------------------------------------------
CATEGORY_USE_LINE = {
    "smart_display": "Useful for hands-free recipe display, family scheduling, video calls, and smart-home routines.",
    "water_bottle":  "Designed for daily hydration, gym, outdoor, or office use.",
    "kitchen_organizer": "Helps keep kitchen drawers, cabinets, or countertops organised and easy to navigate.",
}


def synth_description(p: dict) -> str:
    title = (p.get("title") or "").strip()
    cat   = p.get("category", "")
    use   = CATEGORY_USE_LINE.get(cat, "")
    rating = p.get("rating")
    rc     = p.get("review_count")
    review_part = ""
    if rating and rc:
        review_part = f" Rated {rating:.1f}★ across {rc} customer reviews."
    return f"{title}.{review_part} {use}".strip()


# ----------------------------------------------------------------------------
# Deterministic delivery estimate for Target products. Hash the product_url
# to pick a value in [2, 4] inclusive — stable across runs.
# ----------------------------------------------------------------------------
def deterministic_delivery_days(p: dict) -> int:
    seed = (p.get("product_url") or p.get("title") or "").encode("utf-8")
    h = int(hashlib.md5(seed).hexdigest(), 16)
    return 2 + (h % 3)  # 2, 3, or 4


# ----------------------------------------------------------------------------
# Median rating / review_count per category — used for the 2 missing rows.
# ----------------------------------------------------------------------------
def category_medians(prods: list[dict]) -> dict[str, dict]:
    out: dict[str, dict] = {}
    cats = {p["category"] for p in prods}
    for cat in cats:
        ratings = [p["rating"] for p in prods if p["category"] == cat and p.get("rating")]
        rcs     = [p["review_count"] for p in prods if p["category"] == cat and p.get("review_count")]
        out[cat] = {
            "rating":       round(statistics.median(ratings), 1) if ratings else 4.5,
            "review_count": int(statistics.median(rcs)) if rcs else 100,
        }
    return out


def backfill(prods: list[dict]) -> dict:
    medians = category_medians(prods)
    counters = {
        "description_added": 0,
        "delivery_estimated": 0,
        "rating_filled":      0,
        "review_count_filled": 0,
    }

    for p in prods:
        # description (always synthesized from title + use line; original is null)
        if not p.get("description"):
            p["description"] = synth_description(p)
            p["description_source"] = "synthesized_from_title"
            counters["description_added"] += 1

        # arrival_time_days (only for products without a scraped value)
        if p.get("arrival_time_days") is None:
            p["arrival_time_days"] = deterministic_delivery_days(p)
            p["arrival_time_days_source"] = "estimated"
            counters["delivery_estimated"] += 1
        else:
            p.setdefault("arrival_time_days_source", "scraped")

        # rating (rare — only 2 rows)
        if p.get("rating") is None:
            p["rating"] = medians[p["category"]]["rating"]
            p["rating_source"] = "category_median"
            counters["rating_filled"] += 1
        else:
            p.setdefault("rating_source", "scraped")

        # review_count (rare — only 2 rows)
        if p.get("review_count") is None:
            p["review_count"] = medians[p["category"]]["review_count"]
            p["review_count_source"] = "category_median"
            counters["review_count_filled"] += 1
        else:
            p.setdefault("review_count_source", "scraped")

    return counters


def main() -> None:
    with DATA_PATH.open(encoding="utf-8") as f:
        prods = json.load(f)

    counters = backfill(prods)

    with DATA_PATH.open("w", encoding="utf-8") as f:
        json.dump(prods, f, indent=2, ensure_ascii=False)

    print(f"backfilled {DATA_PATH}")
    for k, v in counters.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
