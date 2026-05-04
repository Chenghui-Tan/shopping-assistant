# backend/main.py
import sys
from pathlib import Path

# Add recommendation engine to path and fix its data path
_ENGINE_DIR = Path(__file__).parent.parent / "recommendation_Algorithem"
sys.path.insert(0, str(_ENGINE_DIR))
import recommendation_engine_refactored as engine
engine.DATA_PATH = Path(__file__).parent.parent / "data" / "clean" / "products_clean.json"

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError

import session as session_store
import claude_client
from questions import (
    get_question_queue, get_question,
    CHIP_TO_VALUE, CATEGORY_ALIASES, CATEGORY_CHIPS,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request models ---

class StartBody(BaseModel):
    text: str

class AnswerBody(BaseModel):
    session_id: str
    question_key: str
    # answer accepts a single chip label, free text, or a list of chip
    # labels (for multi-select questions like smart_display.use_case).
    answer: str | list[str]
    is_chip: bool = False

class RecommendBody(BaseModel):
    session_id: str

class RefineBody(BaseModel):
    session_id: str
    text: str


# Schema we expect Claude's parse_supplement to return. Anything outside
# this shape is rejected so a hallucinated `{insulated: "maybe"}` cannot
# silently corrupt the engine's preference dict.
class _SupplementUpdates(BaseModel):
    """Only fields the ranker recognises. Extra fields are dropped."""
    use_case:          str | list[str] | None = None
    use_area:          str | None = None
    pain_point:        str | None = None
    structure_type:    str | None = None
    insulated:         bool | None = None
    size_preference:   str | None = None
    easy_clean:        bool | None = None
    easy_install:      bool | None = None
    price_max:         float | int | None = None
    delivery_days_max: float | int | None = None
    priority:          str | None = None
    model_config = {"extra": "ignore"}


class _SupplementResponse(BaseModel):
    preference_updates: _SupplementUpdates = Field(default_factory=_SupplementUpdates)
    ai_response: str = ""
    model_config = {"extra": "ignore"}


import re as _re

# Deterministic parser for common refinement phrases. Used when the LLM
# is unreachable (placeholder API key) or returns empty / invalid data,
# so the refine bar still has visible effect on recommendations. Each
# match is keyed off the user's *current* category so the same word
# means the right thing in different contexts (e.g. 'plastic' is a
# bottle material AND an organiser material).

# (regex, key, value) — order matters: first match wins per key. Keys
# follow the same vocabulary the engine reads from preferences.
_SUPP_RULES_GLOBAL: list[tuple[str, str, object]] = [
    # Price ceilings: 'under $80', 'less than $100', '$50 max', '$50 or less'
    (r"(?:under|less than|below|cheaper than)\s*\$?\s*(\d+)",      "price_max", "_int"),
    (r"\$?\s*(\d+)\s*(?:max|maximum|or less|cap|budget)",           "price_max", "_int"),
    # Delivery
    (r"\b(?:asap|today|tomorrow|fast|fastest)\s+delivery\b",       "delivery_days_max", 2),
    (r"\bthis\s+week\b",                                            "delivery_days_max", 7),
    # Privacy / camera (smart_display)
    (r"\bno\s+camera\b|\bwithout\s+camera\b|\bcamera[-\s]?free\b", "privacy_camera",  "no_camera"),
    (r"\bcamera\s+ok\b|\bcamera\s+is\s+fine\b",                    "privacy_camera",  "ok"),
    # Voice ecosystem (smart_display)
    (r"\b(?:works\s+with\s+)?google\b|\bnest\s+hub\b",             "voice_ecosystem", "google"),
    (r"\b(?:works\s+with\s+)?alexa\b|\becho\s+show\b",             "voice_ecosystem", "alexa"),
    (r"\b(?:works\s+with\s+)?apple\b|\bhomepod\b|\bsiri\b",        "voice_ecosystem", "apple"),
    # Leak-proof (water_bottle) — implicit signal
    (r"\bleak[-\s]?proof\b|\bno\s+(?:spill|leak)\b|\bspillproof\b","leak_proof_preferred", True),
    (r"\bleaks?\b|\bspills?\b",                                    "leak_proof_preferred", True),
]

# Category-specific rules — applied only when session category matches.
_SUPP_RULES_BY_CAT: dict[str, list[tuple[str, str, object]]] = {
    "smart_display": [
        # Screen size priority
        (r"\blarger?\s+screen\b|\bbigger\s+screen\b|\b15\b|\b21\b", "screen_size_priority", "large"),
        (r"\bsmaller\s+screen\b|\bcompact\b|\bsmall\s+counter\b",  "screen_size_priority", "compact"),
        (r"\bmid\b|\b8\s*inch\b|\b10\s*inch\b|\b11\s*inch\b",       "screen_size_priority", "mid"),
        # Placement
        (r"\bwall[-\s]?(mount|mountable)\b",                        "placement", "wall"),
        (r"\bkitchen\s+counter\b|\bkitchen\b",                      "placement", "kitchen"),
        (r"\bliving\s+room\b",                                      "placement", "living_room"),
        (r"\bbedroom\b",                                            "placement", "bedroom"),
        # Use case (multi-select-aware)
        (r"\bcooking\b|\brecipe\b",                                 "use_case", "cooking"),
        (r"\bfamily\s+calendar\b|\bcalendar\b|\bschedule\b",        "use_case", "family"),
        (r"\bentertain(?:ment)?\b|\bstreaming\b|\bvideos?\b",       "use_case", "entertainment"),
        (r"\bsmart\s+home\b|\bcontrol\s+lights\b",                  "use_case", "smart_home"),
    ],
    "water_bottle": [
        # Size
        (r"\blarger?\b|\bbigger\b|\bmore\s+capacity\b|\b32\s*oz\b|\b40\s*oz\b|\b64\s*oz\b",
                                                                    "size_preference", "large"),
        (r"\blightweight\b|\blight\b|\bportable\b|\bsmaller\b",     "size_preference", "lightweight"),
        # Insulation
        (r"\binsulated\b|\bdouble[-\s]wall\b|\bvacuum\b|\bkeeps?\s+(?:cold|hot)\b",
                                                                    "insulated", True),
        (r"\bnot?\s+insulated\b|\bplain\s+plastic\b",               "insulated", False),
        # Material
        (r"\bstainless\b|\bsteel\b|\bmetal\s+bottle\b",             "material_preference", "stainless"),
        (r"\bbpa[-\s]?free\b|\btritan\b|\bplastic\b",               "material_preference", "plastic"),
        # Drinking style
        (r"\bfreesip\b|\bhybrid\b",                                 "drinking_style", "freesip"),
        (r"\bstraw\b",                                              "drinking_style", "straw"),
        (r"\bspout\b|\bsippy\b",                                    "drinking_style", "kids"),
        (r"\bstandard\s+cap\b|\bscrew\s+cap\b",                     "drinking_style", "standard"),
        # Use case
        (r"\bgym\b|\bworkout\b|\btraining\b",                       "use_case", "gym"),
        (r"\boutdoor\b|\bhik(?:e|ing)\b|\btrail\b",                 "use_case", "outdoor"),
        (r"\bkids?\b|\bchildren\b|\bschool\b",                      "use_case", "kids"),
        (r"\bdaily\b|\beveryday\b|\boffice\b|\bdesk\b",             "use_case", "daily"),
    ],
    "kitchen_organizer": [
        # Structure
        (r"\bstackable\b|\btier\b|\b3[-\s]?tier\b",                 "structure_type", "stackable"),
        (r"\bdrawer\b|\bflatware\b|\bcompartment\b",                "structure_type", "drawer"),
        (r"\bbin\b|\bbasket\b",                                     "structure_type", "bin"),
        (r"\bexpandable\b|\bmodular\b",                             "structure_type", "expandable"),
        (r"\blazy\s+susan\b|\bturn\s+table\b",                      "structure_type", "lazy_susan"),
        # Material
        (r"\bbamboo\b|\bwood(?:en)?\b",                             "organizer_material", "bamboo"),
        (r"\bmetal\b|\bsteel\b|\bwire\b",                           "organizer_material", "metal"),
        (r"\bplastic\b|\bpetg\b",                                   "organizer_material", "plastic"),
        # Visibility
        (r"\bclear\b|\btransparent\b|\bsee[-\s]?through\b",         "visibility_priority", "clear"),
        (r"\bopaque\b|\bsolid\b",                                   "visibility_priority", "opaque"),
        # Area
        (r"\bcabinets?\b|\bshelves?\b",                             "use_area", "cabinet"),
        (r"\bcounter(?:top)?\b",                                    "use_area", "countertop"),
        (r"\bunder\s+(?:the\s+)?sink\b",                            "use_area", "under_sink"),
        # Pain
        (r"\bnot\s+enough\s+space\b|\btight\b|\bcrammed\b",         "pain_point", "not_enough_space"),
        (r"\bhard\s+to\s+find\b|\blose\s+(?:it|things)\b|\bvisib",   "pain_point", "hard_to_find_things"),
    ],
}


def _deterministic_parse_supplement(text: str, category: str | None) -> dict:
    """Pattern-match the user's refine text into preference updates.

    Returns {preference_updates: {...}, ai_response: '...'} matching the
    contract of claude_client.parse_supplement. Empty updates dict means
    'nothing recognised' — caller should keep prior preferences.
    """
    if not text:
        return {"preference_updates": {}, "ai_response": ""}
    lower = text.lower()
    updates: dict = {}

    # Helper: apply rules in order; first match per key wins.
    def apply(rules: list[tuple[str, str, object]]) -> None:
        for pat, key, val in rules:
            if key in updates:
                continue
            m = _re.search(pat, lower)
            if not m:
                continue
            if val == "_int":
                try:
                    updates[key] = int(m.group(1))
                except (IndexError, ValueError):
                    continue
            else:
                updates[key] = val

    apply(_SUPP_RULES_GLOBAL)
    apply(_SUPP_RULES_BY_CAT.get(category or "", []))

    # Construct an honest acknowledgement so the user sees what changed.
    if updates:
        bits = []
        for k, v in updates.items():
            label = {
                "price_max": f"max price ${v}",
                "delivery_days_max": f"delivery ≤ {v}d",
                "screen_size_priority": f"screen: {v}",
                "voice_ecosystem": f"ecosystem: {v}",
                "privacy_camera": "privacy: no camera" if v == "no_camera" else f"privacy: {v}",
                "leak_proof_preferred": "leak-resistant",
                "size_preference": f"size: {v}",
                "insulated": "insulated" if v else "no insulation",
                "material_preference": f"material: {v}",
                "drinking_style": f"drinking: {v}",
                "use_case": f"use: {v}",
                "placement": f"placement: {v}",
                "structure_type": f"structure: {v}",
                "organizer_material": f"material: {v}",
                "visibility_priority": f"visibility: {v}",
                "use_area": f"area: {v}",
                "pain_point": f"pain: {v}",
            }.get(k, f"{k}: {v}")
            bits.append(label)
        ai = "Got it — updating " + ", ".join(bits) + "."
    else:
        ai = (f'Hmm, I couldn\'t pull a structured change from "{text}". '
              "Try phrases like 'under $80', 'larger screen', 'no camera', or 'leakproof'.")

    return {"preference_updates": updates, "ai_response": ai}


def _validated_supplement(raw: dict) -> dict:
    """Validate Claude's parse_supplement output against the schema.

    Returns a dict in the shape the rest of the route expects:
        {"preference_updates": {...}, "ai_response": str}
    On invalid input we drop the preference updates entirely (better to
    keep stale preferences than to corrupt them) and surface a generic
    acknowledgement.
    """
    try:
        validated = _SupplementResponse.model_validate(raw)
    except ValidationError:
        return {
            "preference_updates": {},
            "ai_response": raw.get("ai_response", "Got it — refreshed below.")
                           if isinstance(raw, dict) else "Got it — refreshed below.",
        }
    # exclude_none keeps the engine seeing only fields the user actually changed
    return {
        "preference_updates": validated.preference_updates.model_dump(exclude_none=True),
        "ai_response": validated.ai_response or "Updated below.",
    }


# --- Helpers ---

def _next_question(session: dict) -> dict | None:
    """Return the next unanswered question dict, or None if all done."""
    queue = get_question_queue(session["category"], session["preferences"])
    if not queue:
        return None
    key = queue[0]
    q = get_question(session["category"], key)
    return {"key": key, "text": q["text"], "chips": q["chips"]}


def _attach_tradeoff_labels(picks: list[dict]) -> None:
    """Add factual tradeoff_labels to each pick by comparing them.

    Each label only applies when *true within the actually-shown set*
    (closes the 'Lowest-cost option in your set' lie the user flagged).
    Labels are list-typed so a single pick can carry multiple
    (e.g. 'Cheapest' + 'Most lightweight').
    """
    if not picks:
        return
    for p in picks:
        p.setdefault("tradeoff_labels", [])

    # Cheapest in shown set
    priced = [p for p in picks if p.get("price") is not None]
    if priced:
        cheapest = min(priced, key=lambda x: x["price"])
        # Only label as 'Cheapest' if there's a real spread (>= $2 cheaper).
        others = [p for p in priced if p is not cheapest]
        if others and cheapest["price"] + 2 <= min(o["price"] for o in others):
            cheapest["tradeoff_labels"].append("Cheapest")

    # Most capacity / largest screen / etc.
    cat = picks[0].get("category")
    if cat == "water_bottle":
        with_oz = [p for p in picks if p.get("capacity_oz")]
        if with_oz:
            biggest = max(with_oz, key=lambda x: x["capacity_oz"])
            if any(p.get("capacity_oz", 0) < biggest["capacity_oz"] - 4 for p in with_oz):
                biggest["tradeoff_labels"].append("Most capacity")
        # Most leakproof: pick with leak_proof when others don't have it.
        leakproof = [p for p in picks
                     if (p.get("features") or {}).get("leak_proof")]
        non_leakproof = [p for p in picks
                         if not (p.get("features") or {}).get("leak_proof")]
        if leakproof and non_leakproof:
            for p in leakproof:
                p["tradeoff_labels"].append("Most leakproof")
        # Lightest: smallest capacity wins (proxy for portability).
        if with_oz and len(with_oz) >= 2:
            smallest = min(with_oz, key=lambda x: x["capacity_oz"])
            if any(p.get("capacity_oz", 0) > smallest["capacity_oz"] + 4 for p in with_oz):
                smallest["tradeoff_labels"].append("Most portable")
    elif cat == "smart_display":
        with_screen = [p for p in picks if p.get("screen_inches")]
        if with_screen:
            biggest = max(with_screen, key=lambda x: x["screen_inches"])
            if any(p.get("screen_inches", 0) < biggest["screen_inches"] - 1
                   for p in with_screen):
                biggest["tradeoff_labels"].append("Largest screen")
        no_camera = [p for p in picks if p.get("has_camera") is False]
        cam = [p for p in picks if p.get("has_camera") is True]
        if no_camera and cam:
            for p in no_camera:
                p["tradeoff_labels"].append("No camera")
    elif cat == "kitchen_organizer":
        clear = [p for p in picks if p.get("organizer_visibility") == "clear"]
        opaque = [p for p in picks if p.get("organizer_visibility") == "opaque"]
        if clear and opaque:
            for p in clear:
                p["tradeoff_labels"].append("Most see-through")

    # Highest-rated (when meaningful spread)
    rated = [p for p in picks if p.get("rating")]
    if len(rated) >= 2:
        top = max(rated, key=lambda x: x["rating"])
        if any(p["rating"] < top["rating"] - 0.2 for p in rated):
            top["tradeoff_labels"].append("Highest rated")


def _check(label: str, status: str, detail: str = "") -> dict:
    """Build one row of the preference-match checklist."""
    return {"label": label, "status": status, "detail": detail}


def _preference_checks(p: dict, prefs: dict) -> list[dict]:
    """Return a per-product list of {label, status} for everything the user
    said they cared about. status ∈ {match, miss, unknown}.

    The checklist is the user-facing answer to 'did this honour what I
    said?' Computed at response time so each pick can render the same
    truth the ranker saw.
    """
    cat = p.get("category")
    feats = p.get("_inferred_features") or {}
    out: list[dict] = []

    def status_bool(have: bool | None) -> str:
        if have is True:  return "match"
        if have is False: return "miss"
        return "unknown"

    # Use case (always asked)
    use_case = prefs.get("use_case")
    if use_case:
        # Multi-select: match if ANY of the picked use cases lit a rule.
        wanted = use_case if isinstance(use_case, list) else [use_case]
        matched_any = any(
            f"{u}_suitable" in (p.get("_category_rule_matches") or [])
            or any(rule.startswith(u) for rule in (p.get("_category_rule_matches") or []))
            for u in wanted
        )
        # Heuristic for water_bottle: gym_suitable, daily_use, etc.
        rules = set(p.get("_category_rule_matches") or [])
        wb_use_rule = {"gym": "gym_suitable", "daily": "daily_use",
                       "outdoor": "outdoor_capacity", "kids": "kids_design"}
        for u in wanted:
            if cat == "water_bottle" and wb_use_rule.get(u) in rules:
                matched_any = True
            if cat == "smart_display" and u == "cooking" and "kitchen_hub_or_recipe" in rules:
                matched_any = True
            if cat == "smart_display" and u == "family" and "family_scheduling" in rules:
                matched_any = True
            if cat == "smart_display" and u == "entertainment" and "entertainment_features" in rules:
                matched_any = True
        out.append(_check("Use case fit", "match" if matched_any else "unknown",
                          ", ".join(wanted)))

    # Price
    price_max = prefs.get("price_max")
    if isinstance(price_max, (int, float)):
        ok = p.get("price") is not None and p["price"] <= price_max
        out.append(_check(f"Under ${price_max:g}", "match" if ok else "miss",
                          f"${p['price']:.2f}" if p.get("price") else ""))

    # ── water_bottle ──────────────────────────────────────────────────────
    if cat == "water_bottle":
        if prefs.get("material_preference") and prefs["material_preference"] != "any":
            target = prefs["material_preference"]
            actual = p.get("bottle_material")
            if actual is None:
                out.append(_check(f"Material: {target}", "unknown"))
            else:
                out.append(_check(f"Material: {target}",
                                  "match" if actual == target else "miss", actual))

        if prefs.get("drinking_style") and prefs["drinking_style"] != "any":
            target = prefs["drinking_style"]
            actual = p.get("drinking_style")
            if actual is None:
                out.append(_check(f"Drinking: {target}", "unknown"))
            else:
                out.append(_check(f"Drinking: {target}",
                                  "match" if actual == target else "miss", actual))

        if prefs.get("insulated") is True:
            out.append(_check("Insulated", status_bool(feats.get("insulated"))))
        elif prefs.get("insulated") is False:
            # User said insulation doesn't matter — still report if it has it
            # (information, not a miss).
            if feats.get("insulated"):
                out.append(_check("Insulated", "match", "bonus — wasn't required"))

        size_pref = prefs.get("size_preference")
        if size_pref == "lightweight":
            out.append(_check("Lightweight", status_bool(feats.get("lightweight"))))
        elif size_pref == "large":
            cap = p.get("capacity_oz")
            if cap is not None:
                out.append(_check("Large capacity (≥24oz)",
                                  "match" if cap >= 24 else "miss", f"{cap}oz"))
            else:
                out.append(_check("Large capacity",
                                  "match" if feats.get("large_capacity") else "unknown"))

        if prefs.get("leak_proof_preferred"):
            out.append(_check("Leak-resistant",
                              "match" if feats.get("leak_proof") else "unknown"))

    # ── smart_display ─────────────────────────────────────────────────────
    if cat == "smart_display":
        eco_pref = prefs.get("voice_ecosystem")
        if eco_pref and eco_pref not in ("none", "any"):
            ecos = p.get("ecosystems") or []
            if not ecos:
                out.append(_check(f"Works with {eco_pref.title()}", "unknown"))
            else:
                out.append(_check(f"Works with {eco_pref.title()}",
                                  "match" if eco_pref in ecos else "miss",
                                  ", ".join(ecos)))

        size_pref = prefs.get("screen_size_priority")
        screen = p.get("screen_inches")
        if size_pref == "compact":
            out.append(_check("Compact (<8\")",
                              "unknown" if screen is None else
                              ("match" if screen < 8 else "miss"),
                              f'{screen}"' if screen else ""))
        elif size_pref == "mid":
            out.append(_check('Mid screen (8–11")',
                              "unknown" if screen is None else
                              ("match" if 8 <= screen <= 11 else "miss"),
                              f'{screen}"' if screen else ""))
        elif size_pref == "large":
            out.append(_check('Large screen (15"+)',
                              "unknown" if screen is None else
                              ("match" if screen >= 15 else "miss"),
                              f'{screen}"' if screen else ""))

        if prefs.get("placement") == "wall":
            mount = p.get("mounting") or []
            out.append(_check("Wall-mountable",
                              "match" if "wall" in mount else "unknown"))

        if prefs.get("privacy_camera") == "no_camera":
            cam = p.get("has_camera")
            if cam is False:
                out.append(_check("No camera", "match"))
            elif cam is True:
                out.append(_check("No camera", "miss", "has camera"))
            else:
                out.append(_check("No camera", "unknown"))

    # ── kitchen_organizer ─────────────────────────────────────────────────
    if cat == "kitchen_organizer":
        if prefs.get("organizer_material") and prefs["organizer_material"] != "any":
            target = prefs["organizer_material"]
            actual = p.get("organizer_material")
            if actual is None:
                out.append(_check(f"Material: {target}", "unknown"))
            else:
                out.append(_check(f"Material: {target}",
                                  "match" if actual == target else "miss", actual))

        if prefs.get("visibility_priority") == "clear":
            vis = p.get("organizer_visibility")
            if vis == "clear":
                out.append(_check("Clear / see-through", "match"))
            elif vis == "opaque":
                out.append(_check("Clear / see-through", "miss", "opaque"))
            else:
                out.append(_check("Clear / see-through", "unknown"))

    return out


def _format_product(p: dict, explanation: str) -> dict:
    return {
        "title": p["title"],
        "price": p["price"],
        "rating": p.get("rating"),
        "image_url": p.get("image_url", ""),
        "product_url": p.get("product_url", ""),
        "explanation": explanation,
        # Signals the ranker actually used — surfaced so the frontend can
        # ground its "why this fits" page in the same evidence rather than
        # re-deriving from the product title.
        "category": p.get("category"),
        "arrival_time_days": p.get("arrival_time_days"),
        "rule_matches": p.get("_category_rule_matches", []),
        "features": {k: v for k, v in (p.get("_inferred_features") or {}).items() if v},
        "score": p.get("_score"),
        # Decision-relevant attributes extracted at load time. Frontend
        # uses these for the comparison view + ProductCard chips.
        "screen_inches":      p.get("screen_inches"),
        "ecosystems":         p.get("ecosystems"),
        "has_camera":         p.get("has_camera"),
        "mounting":           p.get("mounting"),
        "capacity_oz":        p.get("capacity_oz"),
        "bottle_material":    p.get("bottle_material"),
        "drinking_style":     p.get("drinking_style"),
        "organizer_material": p.get("organizer_material"),
        "organizer_visibility": p.get("organizer_visibility"),
        # Pick metadata (only present on /session/curated).
        "pick_label":    p.get("pick_label"),
        "pick_reason":   p.get("pick_reason"),
    }


def _run_recommendations(session: dict) -> tuple[list[dict], str]:
    # Merge session.category into the preferences dict the engine expects.
    # The engine resolves category from preferences["category"], but the
    # session stores it as a top-level field for clarity.
    prefs = {**session["preferences"], "category": session["category"]}
    products, relaxation = engine.recommend_with_relaxation(prefs, top_n=12)
    try:
        explanations = claude_client.write_explanations(
            products, session["preferences"], session["raw_input"]
        )
    except Exception:
        # Fall back to the deterministic engine's own explanation so the demo
        # works without an Anthropic API key.
        explanations = [p.get("_explanation", "") for p in products]
    formatted: list[dict] = []
    for i, p in enumerate(products):
        f = _format_product(p, explanations[i])
        f["pref_checks"] = _preference_checks(p, prefs)
        formatted.append(f)
    session_store.set_recommendations(session["session_id"], formatted)
    return formatted, relaxation


# --- Routes ---

def _empathic_reply(category: str, prefs: dict, raw: str) -> str:
    """Build a contextual reply that references what the user actually said.

    Uses inferred preferences if Claude provided them — otherwise falls
    back to a category-default. Replaces the prior 4-string lookup that
    ignored every detail the user typed.
    """
    use_case = prefs.get("use_case")
    if isinstance(use_case, list):
        use_case = use_case[0] if use_case else None

    # 'Just the category name' inputs (e.g. "water bottle") shouldn't get
    # a frustration acknowledgement — they're a category statement, not a
    # complaint. Detect short non-frustration inputs and use a neutral
    # opener that asks for context.
    raw_lower = (raw or "").lower().strip()
    short_input = len(raw_lower.split()) <= 3
    has_pain = any(kw in raw_lower for kw in (
        "frustrat", "annoying", "small", "leak", "spill", "hate", "tired",
        "messy", "chaos", "hunting", "lose", "lost", "heavy", "bulky",
    ))
    if short_input and not has_pain:
        nice = {
            "water_bottle":      "Got it — let's narrow down the right water bottle for you.",
            "smart_display":     "Good — let's find the right smart display for your space.",
            "kitchen_organizer": "Got it — let's find an organiser that fits your kitchen.",
        }
        if category in nice:
            return nice[category] + " A few quick questions next."

    if category == "smart_display":
        if use_case == "cooking":
            return ("That sounds frustrating — cooking with one eye on a tiny phone screen "
                    "is no way to follow a recipe. Let's find a display that can guide you "
                    "hands-free in the kitchen.")
        if use_case == "family":
            return ("A shared family display can save a lot of group-chat back-and-forth. "
                    "Let's find one that handles calendar, reminders, and quick messages.")
        if use_case == "entertainment":
            return ("Got it — you want a screen that's enjoyable to use, not just functional. "
                    "Let's find one with strong streaming + voice support.")
        if use_case == "smart_home":
            return ("A smart-home hub really does change how a home feels. Let's find one "
                    "that talks to your existing devices and centralises voice control.")
        return "That sounds frustrating. Want a larger screen that can guide you hands-free?"

    if category == "water_bottle":
        if use_case == "gym":
            return ("Gym bottles either keep up with you or actively get in the way — let's "
                    "find one that's lightweight, leak-proof, and keeps drinks cold for hours.")
        if use_case == "outdoor":
            return ("For outdoor use the bottle has to earn its place in your bag. Let's find "
                    "one with capacity for long stretches and insulation that holds up.")
        if use_case == "kids":
            return ("Kids' bottles need to be light, drop-proof, and easy to clean. Let's find "
                    "ones they'll actually carry without complaining.")
        return ("I hear you — the right bottle should disappear into your routine. Let's narrow "
                "it down quickly.")

    if category == "kitchen_organizer":
        return ("Mornings should be calm, not stressful. Let's find organisers that make every "
                "utensil and ingredient easy to grab.")

    return "That sounds frustrating. Let's figure out what would actually make this easier."


_CATEGORY_KEYWORD_PATTERNS: dict[str, list[str]] = {
    "water_bottle": [
        r"\bwater\s+bottle\b", r"\bbottle\b", r"\bhydrat", r"\bdrink",
        r"\bowala\b", r"\bstanley\b", r"\bthermos\b", r"\bgym\s+bottle\b",
        r"\bsippy\b", r"\bstraw\b",
    ],
    "smart_display": [
        r"\bsmart\s+display\b", r"\bkitchen\s+display\b", r"\becho\s+show\b",
        r"\bnest\s+hub\b", r"\balexa\b", r"\bgoogle\s+display\b",
        r"\bdigital\s+(?:calendar|frame|planner)\b", r"\btablet\s+stand\b",
        r"\brecipe\s+screen\b",
        # Common "I cook with my phone, the screen is too small" framings.
        # These match smart_display because the natural answer is a kitchen
        # display, not a kitchen organiser.
        r"\bphone\s+screen\b", r"\bscreen\s+(?:too\s+)?small\b",
        r"\bfollow(?:ing)?\s+recipes?\b", r"\brecipes?\s+on\s+(?:my\s+)?phone\b",
        r"\bhands[-\s]?free\s+(?:cooking|recipe)\b",
    ],
    "kitchen_organizer": [
        r"\bkitchen\s+organi[sz]er\b", r"\borgani[sz]er\b", r"\bdrawer\s+organi",
        r"\bcabinet\b", r"\bcountertop\b", r"\bpantry\b", r"\bspice\s+rack\b",
        r"\blazy\s+susan\b", r"\bbrightroom\b",
    ],
}


def _classify_category(text: str) -> str | None:
    """Best-effort category classifier from raw text. Used as a fallback
    when the LLM is unreachable — without this, plain inputs like
    'water bottle' or 'echo show 8' come back as 'unknown' and the user
    sees a generic empathy reply instead of a category-specific one.
    """
    if not text:
        return None
    lower = text.lower()
    # Score each category by how many patterns match. Tied scores prefer
    # smart_display > water_bottle > kitchen_organizer (model fanciness).
    scores = {cat: 0 for cat in _CATEGORY_KEYWORD_PATTERNS}
    for cat, pats in _CATEGORY_KEYWORD_PATTERNS.items():
        for p in pats:
            if _re.search(p, lower):
                scores[cat] += 1
    best_cat = max(scores, key=lambda c: scores[c])
    return best_cat if scores[best_cat] > 0 else None


@app.post("/session/start")
def start_session(body: StartBody):
    # Best-effort LLM parse. If the API key is a placeholder or the call fails
    # for any reason, fall back to letting the user pick a category from chips
    # — the demo must remain usable without external dependencies.
    try:
        parsed = claude_client.parse_initial_input(body.text)
        category = parsed.get("category", "unknown")
        preferences = parsed.get("preferences", {})
    except Exception:
        category = "unknown"
        preferences = {}

    # Deterministic category fallback when the LLM didn't classify it.
    # 'water bottle' as raw input should land on water_bottle directly,
    # not on the generic 'pick a category' chips screen.
    if category in ("unknown", "", None):
        inferred = _classify_category(body.text)
        if inferred:
            category = inferred

    if category == "unknown" or not category:
        category = ""

    # Strip null-valued keys so the frontend's pre-fill logic isn't confused
    # by the LLM returning {"insulated": null, "size_preference": null, …}.
    preferences = {k: v for k, v in preferences.items() if v not in (None, "")}

    # Implicit-preference inference from the raw frustration text. The user
    # rarely sees a "leak-proof" chip but says "leaks in my gym bag" — we
    # honour that signal explicitly and surface it on the checklist later.
    raw_lower = (body.text or "").lower()
    if any(kw in raw_lower for kw in ("leak", "spill")):
        preferences["leak_proof_preferred"] = True
    if any(kw in raw_lower for kw in ("heavy", "weighs", "heavy bag", "bulky")):
        preferences.setdefault("size_preference", "lightweight")

    s = session_store.create_session(body.text, category, preferences)

    if not category:
        return {
            "session_id": s["session_id"],
            "category": None,
            "next_question": None,
            "chips": CATEGORY_CHIPS,
            "preferences": preferences,
            "reply": _empathic_reply("", preferences, body.text),
        }

    return {
        "session_id": s["session_id"],
        "category": category,
        "next_question": _next_question(s),
        "chips": None,
        "preferences": preferences,
        "reply": _empathic_reply(category, preferences, body.text),
    }


@app.post("/session/answer")
def answer_question(body: AnswerBody):
    s = session_store.get_session(body.session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    # Special case: user is picking a category from the category chips.
    # Category is always single-valued — coerce a list to its first element.
    if body.question_key == "category":
        raw = body.answer[0] if isinstance(body.answer, list) else body.answer
        category = CATEGORY_ALIASES.get(raw, raw)
        session_store.update_category(body.session_id, category)
        s = session_store.get_session(body.session_id)
        return {"next_question": _next_question(s)}

    # Map chip answer(s) to structured values. A list of chips becomes a
    # list of resolved values; the engine's category-specific scorers
    # accept either a single value or a list (see _score_smart_display).
    if body.is_chip:
        chip_map = CHIP_TO_VALUE.get(body.question_key, {})
        if isinstance(body.answer, list):
            value = [chip_map.get(a, a) for a in body.answer]
        else:
            value = chip_map.get(body.answer, body.answer)
    else:
        # Free-text answers must be a single string — coerce defensively.
        text = body.answer if isinstance(body.answer, str) else " ".join(body.answer)
        q = get_question(s["category"], body.question_key)
        question_text = q["text"] if q else body.question_key
        try:
            value = claude_client.map_free_text_answer(body.question_key, question_text, text)
        except Exception:
            # Fall back: store the raw text — the engine treats unknowns gracefully.
            value = text

    session_store.update_preferences(body.session_id, {body.question_key: value})
    session_store.record_answer(body.session_id, body.question_key)

    s = session_store.get_session(body.session_id)
    return {"next_question": _next_question(s)}


@app.post("/session/recommend")
def recommend(body: RecommendBody):
    s = session_store.get_session(body.session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    products, relaxation = _run_recommendations(s)
    # Build the 3-card curated picks alongside the full ranking.
    # Frontend Stage 3 leads with the picks; the full list is collapsed
    # below as "all options".
    raw_ranked = [
        {**p, **{k: v for k, v in p.items() if k not in ("explanation",)}}
        for p in products
    ]
    picks_raw = engine.curated_picks(raw_ranked, s["category"])
    # Re-format picks the same way as products (preserves pick_label/reason).
    picks = []
    for p in picks_raw:
        # Find the matching products list entry to preserve its explanation.
        match = next(
            (pp for pp in products if pp["product_url"] == p.get("product_url")),
            None,
        )
        if match:
            picks.append({
                **match,
                "pick_label":  p.get("pick_label"),
                "pick_reason": p.get("pick_reason"),
            })
    # Attach factual trade-off labels (Cheapest, Most capacity, etc.)
    # computed within the actually-shown picks.
    _attach_tradeoff_labels(picks)
    return {
        "products":   products,
        "picks":      picks,
        "relaxation": relaxation,
        # Echo back the user's raw frustration text so the frontend can
        # quote it on the 'Why this fits' page — turns generic explanation
        # bullets into a personalised "You said X, this addresses it".
        "raw_input":  s.get("raw_input"),
    }


@app.post("/session/refine")
def refine(body: RefineBody):
    s = session_store.get_session(body.session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    # Three-tier parse:
    # 1. Best case — Claude extracts structured updates.
    # 2. Validated but empty / Claude unreachable — fall through to a
    #    deterministic regex parser so common phrases ("under $80",
    #    "larger screen", "no camera") still update preferences.
    # 3. Both empty — generic ack, no preference change.
    result = {"preference_updates": {}, "ai_response": ""}
    try:
        raw = claude_client.parse_supplement(body.text, s["preferences"], s["raw_input"])
        result = _validated_supplement(raw)
    except Exception:
        result = {"preference_updates": {}, "ai_response": ""}

    if not result["preference_updates"]:
        # LLM unavailable or LLM didn't extract anything — try the regex parser.
        det = _deterministic_parse_supplement(body.text, s["category"])
        if det["preference_updates"]:
            result = det
        elif not result["ai_response"]:
            result["ai_response"] = det["ai_response"] or (
                f'Got it — "{body.text}". Updated recommendations below.'
            )

    # Capture preferences BEFORE the merge so we can diff. Without this the
    # /refine route silently overwrites prior elicitation — the proposal's
    # 'preference continuity across turns' headline is empty otherwise.
    before = dict(s["preferences"])
    session_store.update_preferences(body.session_id, result["preference_updates"])
    after = session_store.get_session(body.session_id)["preferences"]
    diff  = session_store.diff_preferences(before, after)

    s = session_store.get_session(body.session_id)
    products, relaxation = _run_recommendations(s)
    picks_raw = engine.curated_picks(products, s["category"])
    picks = []
    for p in picks_raw:
        match = next((pp for pp in products if pp["product_url"] == p.get("product_url")), None)
        if match:
            picks.append({**match, "pick_label": p.get("pick_label"),
                          "pick_reason": p.get("pick_reason")})
    _attach_tradeoff_labels(picks)
    session_store.add_supplement_log(body.session_id, body.text, result["ai_response"], diff=diff)

    return {
        "products":     products,
        "picks":        picks,
        "ai_response":  result["ai_response"],
        "relaxation":   relaxation,
        "diff":         diff,
        "history":      s["supplement_log"],
    }


# Lifecycle dashboard for Scene 5. Content is derived from the user's
# elicited preferences, not just their category — so a single user shopping
# for a smart display does NOT see "Soccer practice — Emma".
#
# Each helper returns the same shape: {header, schedule, menu, video, cards}.
# Helpers can branch on any preference the user actually picked; an empty
# branch falls back to the safest universal copy for that category.

def _has(prefs: dict, key: str, *values: str) -> bool:
    """OR-membership across single-value or list-typed prefs."""
    raw = prefs.get(key)
    if not raw:
        return False
    target = set(values)
    if isinstance(raw, list):
        return any(v in target for v in raw)
    return raw in target


def _smart_display_lifecycle(prefs: dict) -> dict:
    is_family       = _has(prefs, "use_case", "family")
    is_cooking      = _has(prefs, "use_case", "cooking")
    is_entertain    = _has(prefs, "use_case", "entertainment")
    is_smart_home   = _has(prefs, "use_case", "smart_home")

    if is_family:
        header = "Kitchen Display — Family"
        schedule = [
            {"time": "9:00 AM",  "label": "Kids' activity drop-off"},
            {"time": "2:00 PM",  "label": "Grocery delivery window"},
            {"time": "6:00 PM",  "label": "Family dinner"},
        ]
    elif is_entertain and not is_cooking:
        header = "Living-Room Display"
        schedule = [
            {"time": "Now",      "label": "Continue last show"},
            {"time": "8:00 PM",  "label": "New episode reminder"},
            {"time": "Later",    "label": "Sync to TV — Netflix queue"},
        ]
    elif is_smart_home:
        header = "Smart-Home Hub"
        schedule = [
            {"time": "7:00 AM",  "label": "Lights on — kitchen + entry"},
            {"time": "Sunset",   "label": "Auto-dim living room"},
            {"time": "11:00 PM", "label": "Lock + thermostat night mode"},
        ]
    else:  # cooking-only or unspecified
        header = "Kitchen Display"
        schedule = [
            {"time": "8:00 AM",  "label": "Today's meal plan"},
            {"time": "12:30 PM", "label": "Lunch prep timer"},
            {"time": "6:30 PM",  "label": "Dinner recipe walkthrough"},
        ]

    menu = ([
        {"meal": "Breakfast", "label": "Greek yogurt & granola"},
        {"meal": "Lunch",     "label": "Chicken salad wrap"},
        {"meal": "Dinner",    "label": "Teriyaki salmon bowl"},
    ] if is_cooking or is_family else [
        {"meal": "Today",   "label": "No menu items added yet"},
        {"meal": "Tip",     "label": "Tap to enable meal planning"},
        {"meal": "Tonight", "label": "Free time — no scheduled cook"},
    ])

    if is_cooking:
        video = {"title": "Cooking show: Quick weeknight meals",
                 "subtitle": "Watch while preparing dinner"}
    elif is_entertain:
        video = {"title": "Trending: Top streaming pick of the week",
                 "subtitle": "Continue where you left off"}
    elif is_smart_home:
        video = {"title": "Tip: Voice routines you haven't set up",
                 "subtitle": "3-min walkthrough"}
    else:
        video = {"title": "Setup: Make this display yours in 5 minutes",
                 "subtitle": "Quick personalisation walkthrough"}

    cards = []
    if is_cooking:
        cards.append({"icon": "🍴", "title": "Meal Planning",
                      "body": "Track nutrition, plan meals, and generate shopping lists automatically."})
    if is_family:
        cards.append({"icon": "👨‍👩‍👧", "title": "Family Hub",
                      "body": "Sync schedules, leave messages, and coordinate family activities in one place."})
    if is_entertain:
        cards.append({"icon": "🎬", "title": "Entertainment",
                      "body": "Cooking shows, video recipes, and music during meal prep."})
    if is_smart_home:
        cards.append({"icon": "💡", "title": "Smart-Home Routines",
                      "body": "Voice-control lights, locks, thermostat, and one-tap morning/evening scenes."})
    # Always show at least three cards so the layout doesn't collapse.
    if len(cards) < 3:
        for fallback in [
            {"icon": "🍴", "title": "Meal Planning",
             "body": "Track nutrition, plan meals, and generate shopping lists automatically."},
            {"icon": "👨‍👩‍👧", "title": "Family Hub",
             "body": "Sync schedules, leave messages, and coordinate family activities in one place."},
            {"icon": "🎬", "title": "Entertainment",
             "body": "Cooking shows, video recipes, and music during meal prep."},
        ]:
            if fallback["title"] not in {c["title"] for c in cards}:
                cards.append(fallback)
            if len(cards) >= 3:
                break

    return {"header": header, "schedule": schedule, "menu": menu,
            "video": video, "cards": cards[:3]}


def _water_bottle_lifecycle(prefs: dict) -> dict:
    """Realistic post-purchase support for a regular (dumb) water bottle.

    The previous version implied automatic refill tracking, which is
    misleading — a normal bottle can't sense anything. The new copy
    is explicit about what's manual vs phone-based vs reorder-driven.
    """
    is_gym     = _has(prefs, "use_case", "gym")
    is_outdoor = _has(prefs, "use_case", "outdoor")
    is_kids    = _has(prefs, "use_case", "kids")

    if is_gym:
        header   = "Gym & Hydration"
        schedule = [
            {"time": "7:00 AM",  "label": "Pre-workout — drink 16oz on waking"},
            {"time": "Workout", "label": "Sip every 15 min during training"},
            {"time": "Post",    "label": "Refill before commute home"},
        ]
        video    = {"title": "Workout hydration: before, during, after",
                    "subtitle": "Evidence-based targets — 3-min watch"}
    elif is_outdoor:
        header   = "Outdoor & Trail"
        schedule = [
            {"time": "Pre-trip", "label": "Fill night before; freeze half"},
            {"time": "On trail", "label": "Sip every 20 min, before thirst"},
            {"time": "Return",   "label": "Rinse + air-dry upside down"},
        ]
        video    = {"title": "Trail tips: capacity vs weight",
                    "subtitle": "How much water for an 8-hour hike"}
    elif is_kids:
        header   = "Kids' Hydration"
        schedule = [
            {"time": "Morning", "label": "Fill at breakfast — pack in bag"},
            {"time": "Lunch",   "label": "Refill at school water fountain"},
            {"time": "After",   "label": "Top up before practice / playdate"},
        ]
        video    = {"title": "Kid-friendly hydration without the sugar",
                    "subtitle": "Simple flavours that get them drinking"}
    else:  # daily
        header   = "Daily Hydration"
        schedule = [
            {"time": "Morning", "label": "Start with a full bottle on the desk"},
            {"time": "Midday",  "label": "Refill before lunch"},
            {"time": "Evening", "label": "Top off; reduce caffeine"},
        ]
        video    = {"title": "How much water do you actually need?",
                    "subtitle": "Evidence-based daily targets"}

    menu = [
        {"meal": "Goal",     "label": "100 oz / day" if not is_kids else "60 oz / day"},
        {"meal": "Self-check", "label": "Pee colour: pale = good, dark = catch up"},
        {"meal": "Tonight",  "label": "Lemon-mint infusion" if not is_kids else "Sliced strawberries in water"},
    ]

    # Cards lean honest: phone / manual / restock — not 'the bottle knows'.
    cards = [
        {"icon": "🔔", "title": "Phone reminders",
         "body": "Set 2-hour reminders on your phone — the bottle is dumb, the schedule is yours."},
    ]
    if is_gym:
        cards.append({"icon": "🎒", "title": "Gym-bag checklist",
                      "body": "Bottle · towel · post-workout snack · lock — never forget the basics."})
        cards.append({"icon": "🔁", "title": "Replacement parts",
                      "body": "FreeSip lids and straws wear out — reorder a 2-pack every 6 months."})
    elif is_outdoor:
        cards.append({"icon": "🗺️", "title": "Trip planner",
                      "body": "Map water sources; estimate refills per hour for your hike length."})
        cards.append({"icon": "🔁", "title": "Replacement parts",
                      "body": "Carry a spare cap and o-ring — small parts, big reliability."})
    elif is_kids:
        cards.append({"icon": "🎨", "title": "Sticker chart",
                      "body": "Print a 'I drank my water' chart; one sticker per refill — kids love it."})
        cards.append({"icon": "🔁", "title": "Spout / straw refresh",
                      "body": "Kids spouts get chewed — keep a spare set on hand."})
    else:
        cards.append({"icon": "📝", "title": "Manual refill log",
                      "body": "Tap +1 in your phone's notes per refill — the simple version of a tracker."})
        cards.append({"icon": "🔁", "title": "Restock lids / straws",
                      "body": "Replacement parts wear faster than the bottle — keep spares."})

    if len(cards) < 3:
        cards.append({"icon": "🍋", "title": "Flavor ideas",
                      "body": "Citrus, cucumber-mint, electrolyte powders — rotate so it doesn't get boring."})
    return {"header": header, "schedule": schedule, "menu": menu,
            "video": video, "cards": cards[:3]}


def _kitchen_organizer_lifecycle(prefs: dict) -> dict:
    is_cabinet   = _has(prefs, "use_area", "cabinet")
    is_counter   = _has(prefs, "use_area", "countertop")
    is_undersink = _has(prefs, "use_area", "under_sink")
    pain_space   = _has(prefs, "pain_point", "not_enough_space")
    pain_find    = _has(prefs, "pain_point", "hard_to_find_things")

    if is_cabinet:
        header = "Cabinet Reset"
        schedule = [
            {"time": "Mon", "label": "Inventory: top shelf, then bottom"},
            {"time": "Wed", "label": "Wipe down + repack stackable bins"},
            {"time": "Sat", "label": "Weekly grocery run"},
        ]
    elif is_counter:
        header = "Counter Routine"
        schedule = [
            {"time": "Daily",  "label": "Clear non-essentials at end of day"},
            {"time": "Wed",    "label": "Wipe down lazy susan + spice rack"},
            {"time": "Sat",    "label": "Restock visible counter items"},
        ]
    elif is_undersink:
        header = "Under-Sink Reset"
        schedule = [
            {"time": "Mon",  "label": "Check bin contents — toss expired"},
            {"time": "Wed",  "label": "Refill cleaning supplies"},
            {"time": "Sat",  "label": "Quick wipe + dry"},
        ]
    else:
        header = "Organised Kitchen"
        schedule = [
            {"time": "Mon", "label": "Pantry restock — check bins"},
            {"time": "Wed", "label": "Wipe down lazy susan"},
            {"time": "Sat", "label": "Weekly grocery run"},
        ]

    menu = [
        {"meal": "Cabinet",   "label": "Stackable bins — clear"   if pain_space else "Layered shelves"},
        {"meal": "Drawer",    "label": "Flatware tray — sorted"   if pain_find  else "Free-flow drawer"},
        {"meal": "Counter",   "label": "Spice lazy susan — visible" if pain_find else "Daily-use only"},
    ]

    video = {"title": "Kitchen reset: 10-minute weekly tidy",
             "subtitle": "A simple routine to keep everything findable"} if pain_find else {
             "title":   "Maximise tight kitchens: vertical-space tricks",
             "subtitle": "Compact ideas for small apartments"}

    cards = [
        {"icon": "🗂️", "title": "Stay Organised",
         "body": "Gentle weekly nudges to reset bins, drawers, and the lazy susan in 10 minutes."},
        {"icon": "🛒", "title": "Smart Restock",
         "body": "Track what's running low and feed it into your shopping list automatically."},
    ]
    if pain_space:
        cards.append({"icon": "📏", "title": "Space Saver",
                      "body": "Suggestions when bins fill up — reorder before chaos returns."})
    elif pain_find:
        cards.append({"icon": "🔍", "title": "Findable Kitchen",
                      "body": "Tap to label compartments; the assistant remembers where things live."})
    else:
        cards.append({"icon": "✨", "title": "Calm Counters",
                      "body": "Keep everyday items visible and the rest tucked away."})
    return {"header": header, "schedule": schedule, "menu": menu,
            "video": video, "cards": cards[:3]}


def _lifecycle_for(session: dict) -> dict:
    cat = session["category"]
    prefs = session["preferences"]
    if cat == "smart_display":
        return _smart_display_lifecycle(prefs)
    if cat == "water_bottle":
        return _water_bottle_lifecycle(prefs)
    if cat == "kitchen_organizer":
        return _kitchen_organizer_lifecycle(prefs)
    # Unknown category — return the smart-display default.
    return _smart_display_lifecycle(prefs)


@app.get("/session/{session_id}/lifecycle")
def lifecycle(session_id: str):
    s = session_store.get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return _lifecycle_for(s)


class SaveBody(BaseModel):
    session_id: str
    product: dict


@app.post("/session/save")
def save(body: SaveBody):
    s = session_store.get_session(body.session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    saved = session_store.save_product(body.session_id, body.product)
    return {"saved": saved, "count": len(saved)}


@app.get("/session/{session_id}/saved")
def get_saved(session_id: str):
    s = session_store.get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"saved": s["saved"], "count": len(s["saved"])}
