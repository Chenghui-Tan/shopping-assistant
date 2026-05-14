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

# Default data location — points at the repo's shared catalogue. The backend
# overrides this (backend/main.py) but the engine should also work standalone
# (`python recommendation_engine_refactored.py`) for diagnostic runs.
DATA_PATH = Path(__file__).parent.parent / "data" / "clean" / "products_clean.json"

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


def _pref_has(preferences: dict[str, Any], key: str, *values: str) -> bool:
    """
    True iff preferences[key] equals any of `values`, OR is a list that
    contains any of them. Lets multi-select questions (e.g. smart-display
    use_case) light up multiple category-specific rules in one pass.
    """
    raw = preferences.get(key)
    if raw is None or raw == "":
        return False
    target = set(values)
    if isinstance(raw, list):
        return any(v in target for v in raw)
    return raw in target


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
        # Leakproof inference: explicit copy + Owala FreeSip (well-known leakproof
        # bottle) + screw-lid descriptors. We surface this as both a feature
        # flag and a checklist row so users see "Leak-resistant: yes / unknown".
        "leak_proof":     has("leak-proof", "leakproof", "leak proof", "leak resistant",
                              "no-spill", "no spill", "spill-proof", "freesip", "screw lid"),
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
    """Load the cleaned product dataset from disk and enrich every row
    with decision-relevant attributes (screen size, ecosystem, camera,
    capacity) extracted from the title at load time. Keeps the JSON
    on-disk minimal while making the engine and frontend share one
    source of truth for these attributes.
    """
    from attributes import extract_all  # local import to avoid cycle
    with open(DATA_PATH, encoding="utf-8") as f:
        rows = json.load(f)
    for r in rows:
        r.update(extract_all(r))
    return rows


# ---------------------------------------------------------------------------
# 2. Filter
# ---------------------------------------------------------------------------

def _coerce_numeric(v: Any) -> float | int | None:
    """Best-effort numeric coercion — drops the constraint on bad input.

    The chip map can leave a free-text value untouched (e.g. an unmapped
    'Under $200' chip stays as a string). Without coercion the comparator
    `price > price_max` crashes. We prefer dropping the filter to crashing
    the route — the user gets *more* results, not zero.
    """
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return v
    return None


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
    price_max = _coerce_numeric(preferences.get("price_max"))
    delivery_max = _coerce_numeric(preferences.get("delivery_days_max"))
    # Privacy is a hard filter: when the user explicitly says 'no camera',
    # we drop any product known to have one. Products with unknown camera
    # status (has_camera == None) get the benefit of the doubt — same
    # pattern as missing delivery data.
    no_camera_required = preferences.get("privacy_camera") == "no_camera"

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

        if no_camera_required and p.get("has_camera") is True:
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
    # use_case is the demo's only multi-select question; the user can pick
    # cooking + family + entertainment together. We OR over picks via
    # _pref_has so each picked use case independently lights up its rules.
    score = 0.0
    matches: list[str] = []

    # Pull extracted attributes (populated by attributes.extract_all()
    # at load time). Missing values stay None and the rule simply doesn't
    # fire — no fabricated defaults.
    screen      = product.get("screen_inches")
    ecosystems  = product.get("ecosystems") or []
    has_camera  = product.get("has_camera")
    mounting    = product.get("mounting") or []

    # ---- New decision-relevant rules -----------------------------------------

    # Voice ecosystem match — the strongest non-budget filter. If the user
    # picked Alexa and the product talks Alexa, big +0.10. If they picked
    # Apple and we don't see Apple, soft penalty since it's a hard miss.
    eco_pref = preferences.get("voice_ecosystem")
    if eco_pref and eco_pref != "none":
        score = _apply_rule(score, matches, eco_pref in ecosystems,
                            f"ecosystem_{eco_pref}", penalty=_SOFT_PENALTY)

    # Placement filter — wall mount only matters when user picked it.
    placement = preferences.get("placement")
    if placement == "wall":
        score = _apply_rule(score, matches, "wall" in mounting, "wall_mountable",
                            penalty=_SOFT_PENALTY)
    elif placement == "kitchen":
        # Kitchen prefers something that won't dominate the counter.
        if screen is not None:
            score = _apply_rule(score, matches, screen <= 11.0, "kitchen_friendly_size")

    # Screen size priority — gradient scoring so partial-credit matches
    # are visible. Without this, when a Show 5 user says 'larger screen'
    # the Show 8 doesn't outrank Show 5 because both lose the same flat
    # penalty for being < 15". Now Show 5 gets a larger penalty than
    # Show 8 when 'large' is requested, so the ranking actually changes.
    size_pref = preferences.get("screen_size_priority")
    if size_pref == "compact" and screen is not None:
        if screen <= 8.0:
            score += _RULE_BONUS; matches.append("compact_screen")
        elif screen <= 11.0:
            score -= _SOFT_PENALTY * 0.5      # mild miss
        else:
            score -= _SOFT_PENALTY * 1.5      # hard miss
    elif size_pref == "mid" and screen is not None:
        if 8.0 <= screen <= 11.0:
            score += _RULE_BONUS; matches.append("mid_screen")
        elif 5.0 <= screen < 8.0 or 11.0 < screen <= 13.0:
            score -= _SOFT_PENALTY * 0.5      # near miss
        else:
            score -= _SOFT_PENALTY * 1.5      # hard miss
    elif size_pref == "large" and screen is not None:
        if screen >= 15.0:
            score += _RULE_BONUS; matches.append("large_screen_pref")
        elif screen >= 10.0:
            score += _RULE_BONUS * 0.5        # partial credit (10-14")
            matches.append("medium_large_screen")
        elif screen >= 8.0:
            pass                                # acceptable, no penalty
        else:
            score -= _SOFT_PENALTY * 2          # << 8" is clearly too small
            # Show 5 (5.5") loses 0.10; Show 8 stays neutral; net +0.10
            # swing flips the Best Fit when user says "larger screen".

    # Privacy: penalise products with cameras when user said no.
    privacy = preferences.get("privacy_camera")
    if privacy == "no_camera":
        # has_camera == False is a positive match; True is a soft miss;
        # None (unknown) gets neither.
        if has_camera is False:
            score = _apply_rule(score, matches, True, "no_camera_match")
        elif has_camera is True:
            score -= _SOFT_PENALTY * 2  # stronger penalty: privacy is a hard pref

    if _pref_has(preferences, "use_case", "cooking"):
        # Voice control is critical for hands-free cooking — penalise its absence
        score = _apply_rule(score, matches, features["voice_control"], "voice_control",
                            penalty=_SOFT_PENALTY)
        score = _apply_rule(score, matches,
                            _title_has(product, "kitchen hub", "kitchen", "cook", "recipe", "alexa+"),
                            "kitchen_hub_or_recipe")

    if _pref_has(preferences, "use_case", "family"):
        score = _apply_rule(score, matches,
                            _title_has(product, "chore chart", "calendar", "planner", "family", "schedule"),
                            "family_scheduling")
        score = _apply_rule(score, matches,
                            _title_has(product, "15.6", "15\"", "echo show 15", "echo show 21", "21"),
                            "large_screen")

    if _pref_has(preferences, "use_case", "entertainment"):
        score = _apply_rule(score, matches,
                            _title_has(product, "fire tv", "stream", "video call", "netflix",
                                       "youtube", "prime video"),
                            "entertainment_features")
        # Avoid double-counting large_screen if family already added it.
        if "large_screen" not in matches:
            score = _apply_rule(score, matches,
                                _title_has(product, "15.6", "15\"", "echo show 15", "echo show 21",
                                           "21", "10.1", "11"),
                                "large_screen")

    if _pref_has(preferences, "use_case", "smart_home"):
        # Voice control is core for smart home — penalise its absence
        if "voice_control" not in matches:
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

    # Previously missing — size_preference='large' silently did nothing.
    # Use real capacity_oz when extractable, fall back to the inferred
    # large_capacity flag. Threshold 24oz: anything Owala-24oz and up.
    if size_pref == "large":
        cap = product.get("capacity_oz")
        if cap is not None:
            score = _apply_rule(score, matches, cap >= 24, "large_capacity_pref",
                                penalty=_SOFT_PENALTY)
        else:
            score = _apply_rule(score, matches, features["large_capacity"],
                                "large_capacity_pref", penalty=_SOFT_PENALTY)

    # Leak-proof preference. Detected from the user's raw frustration
    # ('leaks/spills') by the route — a strongest-pain signal that should
    # outrank generic gym fit. Use a 1.5x bonus so leakproof bottles win
    # ties against bottles that only score on use_case alone.
    if preferences.get("leak_proof_preferred"):
        if features["leak_proof"]:
            score += _RULE_BONUS * 1.5
            matches.append("leak_proof_match")
        else:
            score -= _SOFT_PENALTY

    if easy_clean_pref:
        score = _apply_rule(score, matches, features["easy_clean"], "easy_clean",
                            penalty=_SOFT_PENALTY)

    # Material preference — soft penalty on mismatch.
    mat_pref = preferences.get("material_preference")
    if mat_pref and mat_pref != "any":
        prod_mat = product.get("bottle_material")
        if prod_mat is not None:
            score = _apply_rule(score, matches, prod_mat == mat_pref,
                                f"material_{mat_pref}", penalty=_SOFT_PENALTY)

    # Drinking style — soft penalty on mismatch.
    drink_pref = preferences.get("drinking_style")
    if drink_pref and drink_pref != "any":
        prod_style = product.get("drinking_style")
        if prod_style is not None:
            score = _apply_rule(score, matches, prod_style == drink_pref,
                                f"drinking_style_{drink_pref}", penalty=_SOFT_PENALTY)

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

    # Material preference — soft penalty on mismatch.
    mat_pref = preferences.get("organizer_material")
    if mat_pref and mat_pref != "any":
        prod_mat = product.get("organizer_material")
        if prod_mat is not None:
            score = _apply_rule(score, matches, prod_mat == mat_pref,
                                f"organizer_material_{mat_pref}", penalty=_SOFT_PENALTY)

    # Visibility — clear is the most common ask. Use as a soft pref.
    vis_pref = preferences.get("visibility_priority")
    if vis_pref == "clear":
        prod_vis = product.get("organizer_visibility")
        if prod_vis is not None:
            score = _apply_rule(score, matches, prod_vis == "clear",
                                "visibility_clear", penalty=_SOFT_PENALTY)

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


def _is_real_display(p: dict[str, Any]) -> bool:
    """True for actual smart displays (not picture frames or sensors).

    Reads rule_matches under either the engine's underscore-prefixed
    name or the API-formatted name so this works with both raw ranker
    output and route-formatted products.
    """
    rules = p.get("_category_rule_matches") or p.get("rule_matches") or []
    feats = p.get("_inferred_features") or p.get("features") or {}
    return ("display_device" in rules
            and (feats.get("voice_control")
                 or bool(p.get("ecosystems"))))


def curated_picks(
    ranked: list[dict[str, Any]],
    category: str | None,
) -> list[dict[str, Any]]:
    """Return up to three differentiated picks from a ranked list.

    The shape is always: Best Fit, Budget Pick, Stretch Pick. Each pick
    carries a `pick_label` and `pick_reason` so the frontend can render
    badges without re-deriving the differentiation. The "Stretch" pick
    is category-specific:
        smart_display    -> Large Screen Pick
        water_bottle     -> Large Capacity Pick
        kitchen_organizer-> Best Visibility Pick

    De-duplicates by product_url so the same item never appears twice
    on the picks page.
    """
    if not ranked:
        return []

    picks: list[dict[str, Any]] = []
    used: set[str] = set()

    # Score lookup tolerant of both shapes: the raw engine output uses
    # `_score`, but the route hands us already-formatted products where
    # the same number is stored as `score`. Without this fallback the
    # 75 % score-floor on Budget Pick silently collapses to 0.
    def _sc(p: dict) -> float:
        s = p.get("_score")
        return (s if s is not None else p.get("score")) or 0.0

    def add(p: dict, label: str, reason: str) -> None:
        url = p.get("product_url") or p.get("title", "")
        if url in used:
            return
        used.add(url)
        picks.append({**p, "pick_label": label, "pick_reason": reason})

    # 1. Best Fit — highest combined score that survived the strict filter.
    best = ranked[0]
    add(best, "Best Fit", "Highest match score across all your stated preferences.")

    # Build a "comparable" pool — products that share the best fit's
    # category-defining traits. For smart displays that means actual
    # smart displays (not picture frames with screens). This prevents
    # the Budget Pick from offering a sensor and the Stretch Pick from
    # offering a picture frame.
    if category == "smart_display":
        comparable = [p for p in ranked if _is_real_display(p)] or ranked
    else:
        comparable = ranked

    # 2. Budget Pick — cheapest comparable product. Skip the top
    #    candidate (don't repeat Best Fit) and require it to score
    #    within 25% of the top score so we don't suggest something
    #    objectively worse just because it's cheap.
    top_score = _sc(best)
    score_floor = top_score * 0.75
    budget_pool = sorted(
        [p for p in comparable
         if p.get("product_url") != best.get("product_url")
         and _sc(p) >= score_floor],
        key=lambda p: p.get("price") or 1e9,
    )
    if budget_pool:
        cand = budget_pool[0]
        if cand.get("price") is not None and best.get("price") is not None:
            saving = best["price"] - cand["price"]
            if saving >= 5:
                reason = (f"${cand['price']:.0f} — saves ${saving:.0f} vs the best fit "
                          "while still scoring near the top.")
            else:
                reason = (f"${cand['price']:.0f} — comparable in price to the best fit "
                          "but worth a look as a runner-up.")
            add(cand, "Budget Pick", reason)

    # 3. Stretch pick — category-specific. Pulls from the *full*
    #    comparable pool (so a real smart display with a 15"+ screen
    #    can still surface even if user picked a 'mid' size preference).
    stretch = None
    stretch_reason = ""
    label = ""
    if category == "smart_display":
        with_screen = [p for p in comparable if p.get("screen_inches")]
        if with_screen:
            cand = max(with_screen, key=lambda p: p["screen_inches"])
            # Only show the stretch if it's meaningfully larger than Best Fit.
            if (best.get("screen_inches") or 0) + 2 <= cand.get("screen_inches", 0):
                stretch = cand
                stretch_reason = (f'{cand["screen_inches"]:.1f}" screen — '
                                  "easier to follow recipes from across the kitchen.")
                label = "Large Screen Pick"
    elif category == "water_bottle":
        with_oz = [p for p in comparable if p.get("capacity_oz")]
        if with_oz:
            cand = max(with_oz, key=lambda p: p["capacity_oz"])
            if (best.get("capacity_oz") or 0) + 8 <= cand.get("capacity_oz", 0):
                stretch = cand
                stretch_reason = (f"{cand['capacity_oz']}oz capacity — fewer refills "
                                  "for long workouts or trips.")
                label = "Large Capacity Pick"
    elif category == "kitchen_organizer":
        vis = [p for p in comparable
               if any(kw in (p.get("title") or "").lower()
                      for kw in ["clear", "compartment", "drawer", "transparent"])]
        if vis:
            stretch = max(vis, key=lambda p: p.get("rating") or 0)
            stretch_reason = ("Clear / compartmented build — every item visible "
                              "and reachable at a glance.")
            label = "Best Visibility Pick"

    if stretch is not None and label and stretch.get("product_url") not in used:
        add(stretch, label, stretch_reason)

    return picks


def recommend_with_relaxation(
    preferences: dict[str, Any],
    top_n: int = 10,
) -> tuple[list[dict[str, Any]], str]:
    """Same as recommend_products, but also returns which fallback fired.

    Returns a (products, relaxation_tier) tuple where relaxation_tier is one of:
        "strict"       – all filters honoured (best case)
        "no_delivery"  – delivery_days_max dropped to find more matches
        "no_price"     – price_max + delivery_days_max dropped (category only)
        "no_category"  – everything dropped; ranked by shared score across catalog

    The frontend uses this to render a banner so the user knows their
    constraints were softened — no silent degradation.
    """
    products = load_products()

    result = _try_ranked(products, preferences, top_n)
    if result is not None:
        return result, "strict"

    relaxed = {k: v for k, v in preferences.items() if k != "delivery_days_max"}
    result = _try_ranked(products, relaxed, top_n)
    if result is not None:
        return result, "no_delivery"

    relaxed = {k: v for k, v in preferences.items()
               if k not in ("delivery_days_max", "price_max")}
    result = _try_ranked(products, relaxed, top_n)
    if result is not None:
        return result, "no_price"

    base_prefs = {"priority": preferences.get("priority", _DEFAULT_PRIORITY)}
    all_with_price = [p for p in products if p.get("price") is not None]
    ranked = rank_products(all_with_price, base_prefs)
    return ranked[:top_n], "no_category"


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
