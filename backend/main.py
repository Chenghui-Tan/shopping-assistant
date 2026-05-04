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
    formatted = [_format_product(p, explanations[i]) for i, p in enumerate(products)]
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

    if category == "unknown" or not category:
        category = ""

    # Strip null-valued keys so the frontend's pre-fill logic isn't confused
    # by the LLM returning {"insulated": null, "size_preference": null, …}.
    preferences = {k: v for k, v in preferences.items() if v not in (None, "")}

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

    try:
        raw = claude_client.parse_supplement(body.text, s["preferences"], s["raw_input"])
        result = _validated_supplement(raw)
    except Exception:
        # Without LLM access, treat the user's supplement as an acknowledged note
        # and re-run recommendations against the same preferences.
        result = {
            "preference_updates": {},
            "ai_response": f'Got it — "{body.text}". Updated recommendations below.',
        }

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
    is_gym     = _has(prefs, "use_case", "gym")
    is_daily   = _has(prefs, "use_case", "daily")
    is_outdoor = _has(prefs, "use_case", "outdoor")
    is_kids    = _has(prefs, "use_case", "kids")

    if is_gym:
        header   = "Gym & Hydration"
        schedule = [
            {"time": "7:00 AM",  "label": "Morning workout — 32oz before"},
            {"time": "12:30 PM", "label": "Refill at lunch"},
            {"time": "5:00 PM",  "label": "Evening run"},
        ]
        video    = {"title": "Workout reminder: Hydrate before, during, after",
                    "subtitle": "Coaching tips synced to your run"}
    elif is_outdoor:
        header   = "Outdoor & Trail"
        schedule = [
            {"time": "Pre-trip", "label": "Fill 64oz; freeze half overnight"},
            {"time": "On trail", "label": "Sip every 20 min — stay ahead of thirst"},
            {"time": "Return",   "label": "Rinse, air-dry, restock"},
        ]
        video    = {"title": "Trail tips: Carry capacity vs weight",
                    "subtitle": "How much water for an 8-hour hike"}
    elif is_kids:
        header   = "Kids' Hydration"
        schedule = [
            {"time": "8:00 AM",  "label": "Pack with breakfast — fill at the bus stop"},
            {"time": "12:00 PM", "label": "Lunchtime refill at school"},
            {"time": "5:30 PM",  "label": "After-school sport — sip every 20 min"},
        ]
        video    = {"title": "Kid-friendly hydration without the sugar",
                    "subtitle": "Simple flavours that get them drinking water"}
    else:  # daily / default
        header   = "Daily Hydration"
        schedule = [
            {"time": "Morning",  "label": "Start with a full bottle on the desk"},
            {"time": "Midday",   "label": "Refill before lunch"},
            {"time": "Evening",  "label": "Top off; reduce caffeine"},
        ]
        video    = {"title": "How much water do you actually need?",
                    "subtitle": "Evidence-based daily targets"}

    menu = [
        {"meal": "Goal",     "label": "100 oz / day" if not is_kids else "60 oz / day"},
        {"meal": "Reminder", "label": "Sip every 20 minutes"},
        {"meal": "Tonight",  "label": "Lemon-mint infusion" if not is_kids else "Sliced strawberries in water"},
    ]

    cards = [
        {"icon": "💧", "title": "Hydration Tracker",
         "body": "Log every refill; nudges you when you're falling behind your goal."},
    ]
    if is_gym:
        cards.append({"icon": "🏃", "title": "Workout Companion",
                      "body": "Sync sessions and remind you to top up before/during/after each workout."})
    if is_outdoor:
        cards.append({"icon": "🧭", "title": "Trip Planner",
                      "body": "Estimate carry capacity for hikes; auto-tracks usage rate."})
    if is_kids:
        cards.append({"icon": "🎨", "title": "Kid Mode",
                      "body": "Colour-coded refills, gentle reminders, and progress stickers."})
    if len(cards) < 3:
        cards.append({"icon": "🍋", "title": "Flavor Ideas",
                      "body": "Citrus, herbal, and electrolyte rotations so plain water never gets boring."})
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
