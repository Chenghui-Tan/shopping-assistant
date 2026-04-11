"""
Recommendation engine for the shopping assistant.

Pipeline: load → filter → score_shared + score_category_specific → rank → recommend

This is the refactored version of recommendation_engine.py.
Changes from the original:
  - Added _apply_rule() helper to remove repeated if/else scoring blocks
  - Added _try_ranked() helper to remove repeated fallback pattern in recommend_products()
  - Extracted soft-penalty magic number into _SOFT_PENALTY constant
  - All business logic, scoring rules, output format, and fallback order are unchanged

Usage:
    python recommendation_engine_refactored.py

Or import and call directly:
    from recommendation_engine_refactored import recommend_products
    results = recommend_products({"category": "smart_display", "price_max": 150})
"""
from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

from explainability import generate_explanation

DATA_PATH = Path(__file__).parent / "data" / "clean" / "products_clean.json"

# Category aliases so callers can use natural language or snake_case
CATEGORY_ALIASES: dict[str, str] = {
    "smart display":      "smart_display",
    "smart_display":      "smart_display",
    "smart displays":     "smart_display",
    "kitchen display":    "smart_display",
    "water bottle":       "water_bottle",
    "water_bottle":       "water_bottle",
    "water bottles":      "water_bottle",
    "kitchen organizer":  "kitchen_organizer",
    "kitchen_organizer":  "kitchen_organizer",
    "kitchen organizers": "kitchen_organizer",
    "organizer":          "kitchen_organizer",
}

# Shared scoring weights by priority mode (each set must sum to 1.0)
WEIGHTS_BY_PRIORITY: dict[str, dict[str, float]] = {
    "balanced":      {"rating": 0.4, "price": 0.3, "delivery": 0.3},
    "budget":        {"rating": 0.2, "price": 0.6, "delivery": 0.2},
    "quality":       {"rating": 0.6, "price": 0.2, "delivery": 0.2},
    "fast_delivery": {"rating": 0.3, "price": 0.2, "delivery": 0.5},
}
_DEFAULT_PRIORITY = "balanced"

# Score bonus added per matched category rule
_RULE_BONUS = 0.10

# Score reduction when a user-requested feature is absent (soft penalty)
_SOFT_PENALTY = 0.05


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_category(preferences: dict[str, Any]) -> str | None:
    raw = preferences.get("category", "")
    return CATEGORY_ALIASES.get(raw.lower().strip()) if raw else None


def _title_has(product: dict[str, Any], *keywords: str) -> bool:
    """Return True if any keyword appears in the product title (case-insensitive)."""
    title = (product.get("title") or "").lower()
    return any(kw.lower() in title for kw in keywords)


def _apply_rule(
    score: float,
    matches: list[str],
    condition: bool,
    label: str,
    *,
    penalty: float = 0.0,
) -> float:
    """
    Apply a single scoring rule and return the updated score.

    If condition is True:  add _RULE_BONUS and record label in matches.
    If condition is False: optionally subtract penalty (default: no penalty).

    Keeping this small and explicit makes each call site easy to read
    and avoids burying business logic in config structures.
    """
    if condition:
        score += _RULE_BONUS
        matches.append(label)
    elif penalty:
        score -= penalty
    return score


def infer_features(product: dict[str, Any]) -> dict[str, bool]:
    """
    Infer boolean feature flags from title and description via keyword matching.
    Used when structured product attributes are absent.
    """
    text = (
        (product.get("title") or "") + " " + (product.get("description") or "")
    ).lower()

    def has(*kws: str) -> bool:
        return any(kw in text for kw in kws)

    return {
        "insulated":      has("insulated", "vacuum", "double wall", "thermos"),
        "easy_clean":     has("dishwasher", "easy clean", "bpa-free", "freesip", "pop and fill"),
        "stackable":      has("stackable"),
        "expandable":     has("expandable"),
        "drawer_style":   has("drawer"),
        "voice_control":  has("alexa", "echo", "google assistant", "smart display",
                              "nest hub", "echo show"),
        "large_capacity":    has("large", "32oz", "40oz", "64oz", "xl"),
        "lightweight":       has("lightweight", "light weight", "16oz", "18oz", "19oz",
                                 "22oz", "24oz", "plastic", "tritan"),
        "is_display_device": (
            has("echo show", "nest hub", "smart display", "google display", "alexa display",
                "digital picture frame", "digital photo frame", "digital calendar",
                "wall planner", "picture frame")
            and not has("sensor", "humidity", "temperature sensor", "motion sensor")
        ),
    }


# ---------------------------------------------------------------------------
# 1. Load
# ---------------------------------------------------------------------------

def load_products() -> list[dict[str, Any]]:
    """Load the cleaned product dataset from disk."""
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# 2. Filter
# ---------------------------------------------------------------------------

def filter_products(
    products: list[dict[str, Any]],
    preferences: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Filter products by hard constraints in preferences:
        category          – canonical name or alias (required for useful results)
        price_max         – maximum price (inclusive); products with no price are excluded
        delivery_days_max – maximum arrival_time_days (inclusive);
                            products with no delivery data are kept (benefit of the doubt)
    """
    category  = _resolve_category(preferences)
    price_max = preferences.get("price_max")
    delivery_max = preferences.get("delivery_days_max")

    result = []
    for p in products:
        if category and p.get("category") != category:
            continue

        price = p.get("price")
        if price is None:
            continue
        if price_max is not None and price > price_max:
            continue

        if delivery_max is not None:
            days = p.get("arrival_time_days")
            if days is not None and days > delivery_max:
                continue

        result.append(p)
    return result


# ---------------------------------------------------------------------------
# 3. Shared scoring (price + rating + delivery, normalised within the pool)
# ---------------------------------------------------------------------------

def get_weights(preferences: dict[str, Any]) -> dict[str, float]:
    """Return the weight dict for the priority mode in preferences."""
    priority = preferences.get("priority", _DEFAULT_PRIORITY)
    return WEIGHTS_BY_PRIORITY.get(priority, WEIGHTS_BY_PRIORITY[_DEFAULT_PRIORITY])


def score_shared(
    product: dict[str, Any],
    weights: dict[str, float],
    *,
    price_min: float,
    price_max_observed: float,
    rating_min: float,
    rating_max: float,
    delivery_min: float,
    delivery_max_observed: float,
) -> float:
    """
    Return a composite score in [0, 1] using pool-normalised sub-scores.

    Price score:    1 = cheapest in pool, 0 = most expensive
    Rating score:   1 = highest rated,   0 = lowest rated
    Delivery score: 1 = fastest, 0 = slowest; null delivery gets a neutral 0.5
    """
    # Price (lower is better)
    price = product["price"]
    price_range = price_max_observed - price_min
    price_score = (1.0 - (price - price_min) / price_range) if price_range > 0 else 1.0

    # Rating (higher is better)
    rating = product.get("rating") or rating_min
    rating_range = rating_max - rating_min
    rating_score = ((rating - rating_min) / rating_range) if rating_range > 0 else 1.0

    # Delivery (shorter is better; None → neutral 0.5)
    days = product.get("arrival_time_days")
    if days is None:
        delivery_score = 0.5
    else:
        delivery_range = delivery_max_observed - delivery_min
        delivery_score = (1.0 - (days - delivery_min) / delivery_range) if delivery_range > 0 else 1.0

    return (
        weights["price"]    * price_score
        + weights["rating"] * rating_score
        + weights["delivery"] * delivery_score
    )


# ---------------------------------------------------------------------------
# 4. Category-specific scoring (keyword heuristics on title)
# ---------------------------------------------------------------------------

def score_category_specific(
    product: dict[str, Any],
    preferences: dict[str, Any],
    features: dict[str, bool],
) -> tuple[float, list[str]]:
    """
    Return (score_adjustment, matched_rules) for category-specific signals.
    Positive adjustments reward matching features; small negative adjustments
    soft-penalise missing features that the user explicitly requested.
    """
    category = _resolve_category(preferences)
    if category == "smart_display":
        return _score_smart_display(product, preferences, features)
    if category == "water_bottle":
        return _score_water_bottle(product, preferences, features)
    if category == "kitchen_organizer":
        return _score_kitchen_organizer(product, preferences, features)
    return 0.0, []


def _score_smart_display(
    product: dict[str, Any],
    preferences: dict[str, Any],
    features: dict[str, bool],
) -> tuple[float, list[str]]:
    use_case = preferences.get("use_case", "")
    score = 0.0
    matches: list[str] = []

    if use_case == "cooking":
        # Voice control is critical for hands-free cooking — penalise its absence
        score = _apply_rule(score, matches, features["voice_control"], "voice_control",
                            penalty=_SOFT_PENALTY)
        score = _apply_rule(score, matches,
                            _title_has(product, "kitchen hub", "kitchen", "cook", "recipe", "alexa+"),
                            "kitchen_hub_or_recipe")

    elif use_case == "family":
        score = _apply_rule(score, matches,
                            _title_has(product, "chore chart", "calendar", "planner", "family", "schedule"),
                            "family_scheduling")
        score = _apply_rule(score, matches,
                            _title_has(product, "15.6", "15\"", "echo show 15", "echo show 21", "21"),
                            "large_screen")

    elif use_case == "entertainment":
        score = _apply_rule(score, matches,
                            _title_has(product, "fire tv", "stream", "video call", "netflix",
                                       "youtube", "prime video"),
                            "entertainment_features")
        score = _apply_rule(score, matches,
                            _title_has(product, "15.6", "15\"", "echo show 15", "echo show 21",
                                       "21", "10.1", "11"),
                            "large_screen")

    elif use_case == "smart_home":
        # Voice control is core for smart home — penalise its absence
        score = _apply_rule(score, matches, features["voice_control"], "smart_home_compatible",
                            penalty=_SOFT_PENALTY)
        score = _apply_rule(score, matches,
                            _title_has(product, "smart color bulb", "zigbee", "bluetooth",
                                       "tp-link", "sengled", "wiz"),
                            "smart_device_bundle")

    # Category compatibility signal — applied for all smart_display use cases
    score = _apply_rule(score, matches, features["is_display_device"], "display_device")

    return score, matches


def _score_water_bottle(
    product: dict[str, Any],
    preferences: dict[str, Any],
    features: dict[str, bool],
) -> tuple[float, list[str]]:
    use_case        = preferences.get("use_case", "")
    insulated_pref  = preferences.get("insulated", False)
    size_pref       = preferences.get("size_preference", "")
    easy_clean_pref = preferences.get("easy_clean", False)
    score = 0.0
    matches: list[str] = []

    if use_case == "gym":
        score = _apply_rule(score, matches,
                            features["lightweight"] or _title_has(product, "freesip", "owala",
                                                                   "stainless steel"),
                            "gym_suitable")
        score = _apply_rule(score, matches, features["insulated"], "insulated_gym")

    elif use_case == "daily":
        score = _apply_rule(score, matches,
                            _title_has(product, "tritan", "bpa-free", "hydration",
                                       "all in motion", "portable"),
                            "daily_use")

    elif use_case == "outdoor":
        # Large capacity is important for outdoor; penalise small bottles
        score = _apply_rule(score, matches, features["large_capacity"], "outdoor_capacity",
                            penalty=_SOFT_PENALTY)
        # Insulation matters outdoors; penalise non-insulated
        score = _apply_rule(score, matches, features["insulated"], "insulated_outdoor",
                            penalty=_SOFT_PENALTY)

    elif use_case == "kids":
        score = _apply_rule(score, matches,
                            _title_has(product, "kids", "princess", "stitch", "minecraft",
                                       "hello kitty", "sonic", "spider-man", "zak"),
                            "kids_design")
        score = _apply_rule(score, matches, features["lightweight"], "kids_lightweight")

    # Explicit feature flags — reward match, soft-penalise mismatch when preference is set
    if insulated_pref:
        score = _apply_rule(score, matches, features["insulated"], "insulated",
                            penalty=_SOFT_PENALTY)

    if size_pref == "lightweight":
        score = _apply_rule(score, matches, features["lightweight"], "lightweight_size",
                            penalty=_SOFT_PENALTY)

    if easy_clean_pref:
        score = _apply_rule(score, matches, features["easy_clean"], "easy_clean",
                            penalty=_SOFT_PENALTY)

    return score, matches


def _score_kitchen_organizer(
    product: dict[str, Any],
    preferences: dict[str, Any],
    features: dict[str, bool],
) -> tuple[float, list[str]]:
    use_area       = preferences.get("use_area", "")
    pain_point     = preferences.get("pain_point", "")
    structure_type = preferences.get("structure_type", "")
    easy_install   = preferences.get("easy_install", False)
    score = 0.0
    matches: list[str] = []

    if use_area == "cabinet":
        score = _apply_rule(score, matches,
                            _title_has(product, "cabinet", "shelf", "lazy susan", "shelf riser"),
                            "cabinet_fit")
        score = _apply_rule(score, matches,
                            features["stackable"] or features["expandable"],
                            "cabinet_stackable")

    elif use_area == "countertop":
        score = _apply_rule(score, matches,
                            _title_has(product, "counter", "coffee bar", "spice rack",
                                       "lazy susan", "turn table"),
                            "countertop_suitable")
        score = _apply_rule(score, matches,
                            _title_has(product, "decorative", "clear", "modern", "clean"),
                            "countertop_aesthetic")

    elif use_area == "under_sink":
        score = _apply_rule(score, matches,
                            _title_has(product, "bin", "basket", "expandable", "stackable"),
                            "under_sink_fit")

    if pain_point == "not_enough_space":
        # Space-saving is critical here — penalise products that clearly don't help
        score = _apply_rule(score, matches,
                            features["stackable"] or features["expandable"],
                            "space_efficient",
                            penalty=_SOFT_PENALTY)

    if pain_point == "hard_to_find_things":
        score = _apply_rule(score, matches,
                            features["drawer_style"] or _title_has(product, "clear", "compartment"),
                            "visibility_easy_access")

    if structure_type:
        _structure_keywords: dict[str, list[str]] = {
            "stackable":  ["stackable", "tier", "3-tier"],
            "drawer":     ["drawer", "flatware", "compartment"],
            "bin":        ["bin", "basket", "fridge"],
            "expandable": ["expandable"],
            "lazy_susan": ["lazy susan", "turn table"],
        }
        kws = _structure_keywords.get(structure_type.lower(), [structure_type.lower()])
        # User specified a structure type; mismatch is a soft miss
        score = _apply_rule(score, matches, _title_has(product, *kws),
                            f"structure_{structure_type}", penalty=_SOFT_PENALTY)

    if easy_install:
        score = _apply_rule(score, matches,
                            _title_has(product, "expandable", "set", "8pc", "25pc", "modular"),
                            "easy_install")

    return score, matches


# ---------------------------------------------------------------------------
# 5. Combined score
# ---------------------------------------------------------------------------

def score_product(
    product: dict[str, Any],
    preferences: dict[str, Any],
    weights: dict[str, float],
    features: dict[str, bool],
    *,
    price_min: float,
    price_max_observed: float,
    rating_min: float,
    rating_max: float,
    delivery_min: float,
    delivery_max_observed: float,
) -> tuple[float, list[str]]:
    """
    Return (final_score, rule_matches).
    final_score = score_shared + category_specific_adjustment
    """
    shared = score_shared(
        product, weights,
        price_min=price_min,
        price_max_observed=price_max_observed,
        rating_min=rating_min,
        rating_max=rating_max,
        delivery_min=delivery_min,
        delivery_max_observed=delivery_max_observed,
    )
    # For smart_display: non-display devices (sensors, speakers, etc.) get a
    # penalised base score and no category bonuses — they should never surface in
    # results regardless of how cheap/highly-rated they happen to be.
    category = _resolve_category(preferences)
    if category == "smart_display" and not features.get("is_display_device"):
        return shared * 0.65, []

    adjustment, rule_matches = score_category_specific(product, preferences, features)
    return shared + adjustment, rule_matches


# ---------------------------------------------------------------------------
# 6. Rank
# ---------------------------------------------------------------------------

def rank_products(
    products: list[dict[str, Any]],
    preferences: dict[str, Any],
) -> list[dict[str, Any]]:
    """Attach _score, _weights_used, _category_rule_matches, _explanation and sort descending."""
    if not products:
        return []

    prices     = [p["price"] for p in products]
    ratings    = [p.get("rating") or 0.0 for p in products]
    deliveries = [p["arrival_time_days"] for p in products if p.get("arrival_time_days") is not None]

    stats = dict(
        price_min=min(prices),
        price_max_observed=max(prices),
        rating_min=min(ratings),
        rating_max=max(ratings),
        delivery_min=min(deliveries) if deliveries else 0.0,
        delivery_max_observed=max(deliveries) if deliveries else 0.0,
    )

    weights = get_weights(preferences)

    scored = []
    for p in products:
        features = infer_features(p)
        final, rule_matches = score_product(p, preferences, weights, features, **stats)
        explanation = generate_explanation(p, preferences, rule_matches=rule_matches, features=features)
        scored.append({
            **p,
            "_score":                 round(final, 4),
            "_weights_used":          weights,
            "_category_rule_matches": rule_matches,
            "_inferred_features":     features,
            "_explanation":           explanation,
        })

    scored.sort(key=lambda p: p["_score"], reverse=True)
    return scored


# ---------------------------------------------------------------------------
# 7. Recommend
# ---------------------------------------------------------------------------

_MIN_RESULTS = 5  # minimum acceptable result count before triggering fallback


def _try_ranked(
    products: list[dict[str, Any]],
    preferences: dict[str, Any],
    top_n: int,
) -> list[dict[str, Any]] | None:
    """
    Filter → rank → return top_n if results meet the _MIN_RESULTS threshold.
    Returns None when too few products pass the filter, signalling the caller
    to try the next fallback level.
    """
    ranked = rank_products(filter_products(products, preferences), preferences)
    return ranked[:top_n] if len(ranked) >= _MIN_RESULTS else None


def recommend_products(
    preferences: dict[str, Any],
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """
    Full pipeline: load → filter → rank → return top N products.

    Falls back gracefully when strict constraints yield too few results:
      Attempt 1: full constraints (category + price_max + delivery_days_max)
      Fallback 1: drop delivery_days_max
      Fallback 2: drop delivery_days_max + price_max  (category only)
      Fallback 3: all products by shared score  (no category filter)

    preferences keys:
        category          (str)   – "smart display", "water bottle", "kitchen organizer"
        price_max         (float) – upper price bound
        delivery_days_max (int)   – maximum acceptable delivery days
        priority          (str)   – "balanced" | "budget" | "quality" | "fast_delivery"
        use_case          (str)   – category-specific use case
        # smart_display:  use_case in {cooking, family, entertainment, smart_home}
        # water_bottle:   use_case in {gym, daily, outdoor, kids}
        #                 insulated (bool), size_preference (str), easy_clean (bool)
        # kitchen_organizer: use_area in {cabinet, countertop, under_sink}
        #                    pain_point in {not_enough_space, hard_to_find_things}
        #                    structure_type (str), easy_install (bool)
    """
    products = load_products()

    # Attempt 1: full constraints
    result = _try_ranked(products, preferences, top_n)
    if result is not None:
        return result

    # Fallback 1: relax delivery constraint
    relaxed = {k: v for k, v in preferences.items() if k != "delivery_days_max"}
    result = _try_ranked(products, relaxed, top_n)
    if result is not None:
        return result

    # Fallback 2: relax price + delivery (category only)
    relaxed = {k: v for k, v in preferences.items()
               if k not in ("delivery_days_max", "price_max")}
    result = _try_ranked(products, relaxed, top_n)
    if result is not None:
        return result

    # Fallback 3: ignore category — return top products by shared score
    base_prefs = {"priority": preferences.get("priority", _DEFAULT_PRIORITY)}
    all_with_price = [p for p in products if p.get("price") is not None]
    ranked = rank_products(all_with_price, base_prefs)
    return ranked[:top_n]


# ---------------------------------------------------------------------------
# Pretty-print helper
# ---------------------------------------------------------------------------

def print_recommendations(
    preferences: dict[str, Any],
    results: list[dict[str, Any]],
) -> None:
    cat       = preferences.get("category", "all")
    price_max = preferences.get("price_max")
    days_max  = preferences.get("delivery_days_max")
    use_case  = preferences.get("use_case") or preferences.get("use_area", "")

    constraints = []
    if price_max is not None:
        constraints.append(f"price ≤ ${price_max}")
    if days_max is not None:
        constraints.append(f"delivery ≤ {days_max}d")
    if use_case:
        constraints.append(f"use_case: {use_case}")
    constraint_str = ", ".join(constraints) or "none"

    priority   = preferences.get("priority", _DEFAULT_PRIORITY)
    weights    = get_weights(preferences)
    weight_str = (
        f"rating {weights['rating']:.0%}  "
        f"price {weights['price']:.0%}  "
        f"delivery {weights['delivery']:.0%}"
    )

    print(f"\n{'─' * 66}")
    print(f"  Top {len(results)} recommendations — {cat}")
    print(f"  Filters : {constraint_str}")
    print(f"  Priority: {priority}  →  {weight_str}")
    print(f"{'─' * 66}")

    if not results:
        print("  No products matched your preferences.")
        print(f"{'─' * 66}\n")
        return

    for i, p in enumerate(results, 1):
        name     = textwrap.shorten(p["title"], width=55, placeholder="…")
        price    = f"${p['price']:.2f}" if p.get("price") else "N/A"
        rating   = f"{p['rating']:.1f}★" if p.get("rating") else "N/A"
        days     = f"{p['arrival_time_days']}d" if p.get("arrival_time_days") is not None else "N/A"
        platform = p.get("source", "unknown")
        url      = p.get("product_url", "")
        score    = p.get("_score", 0)
        rules    = p.get("_category_rule_matches", [])
        features = p.get("_inferred_features", {})
        explanation = p.get("_explanation", "")

        # Only show inferred features that are True
        active_features = [k for k, v in features.items() if v]

        print(f"\n  {i:>2}. {name}")
        print(f"      Price: {price:<10}  Rating: {rating:<8}  Delivery: {days:<6}  Score: {score:.3f}")
        print(f"      Platform: {platform:<10}  URL: {url[:56]}")
        if active_features:
            print(f"      Inferred : {', '.join(active_features)}")
        if rules:
            print(f"      Rules    : {', '.join(rules)}")
        if explanation:
            wrapped = textwrap.fill(
                explanation, width=60,
                initial_indent="      ", subsequent_indent="      ",
            )
            print(wrapped)

    print(f"\n{'─' * 66}\n")


# ---------------------------------------------------------------------------
# Demo — one example per category
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo_queries = [
        {
            "category": "smart_display",
            "price_max": 150,
            "delivery_days_max": 3,
            "priority": "fast_delivery",
            "use_case": "cooking",
        },
        {
            "category": "water_bottle",
            "price_max": 30,
            "priority": "budget",
            "use_case": "gym",
            "insulated": True,
            "size_preference": "lightweight",
            "easy_clean": True,
        },
        {
            "category": "kitchen_organizer",
            "price_max": 30,
            "priority": "balanced",
            "use_area": "cabinet",
            "pain_point": "not_enough_space",
            "structure_type": "stackable",
            "easy_install": True,
        },
    ]

    for prefs in demo_queries:
        results = recommend_products(prefs, top_n=5)
        print_recommendations(prefs, results)
