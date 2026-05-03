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
from pydantic import BaseModel

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
    answer: str
    is_chip: bool = False

class RecommendBody(BaseModel):
    session_id: str

class RefineBody(BaseModel):
    session_id: str
    text: str


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
    }


def _run_recommendations(session: dict) -> list[dict]:
    # Merge session.category into the preferences dict the engine expects.
    # The engine resolves category from preferences["category"], but the
    # session stores it as a top-level field for clarity.
    prefs = {**session["preferences"], "category": session["category"]}
    products = engine.recommend_products(prefs, top_n=12)
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
    return formatted


# --- Routes ---

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

    s = session_store.create_session(body.text, category, preferences)

    if not category:
        return {
            "session_id": s["session_id"],
            "category": None,
            "next_question": None,
            "chips": CATEGORY_CHIPS,
        }

    return {
        "session_id": s["session_id"],
        "category": category,
        "next_question": _next_question(s),
        "chips": None,
    }


@app.post("/session/answer")
def answer_question(body: AnswerBody):
    s = session_store.get_session(body.session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    # Special case: user is picking a category from the category chips
    if body.question_key == "category":
        category = CATEGORY_ALIASES.get(body.answer, body.answer)
        session_store.update_category(body.session_id, category)
        s = session_store.get_session(body.session_id)
        return {"next_question": _next_question(s)}

    # Map chip answer directly; free-text goes through Claude
    if body.is_chip:
        value = CHIP_TO_VALUE.get(body.question_key, {}).get(body.answer, body.answer)
    else:
        q = get_question(s["category"], body.question_key)
        question_text = q["text"] if q else body.question_key
        try:
            value = claude_client.map_free_text_answer(body.question_key, question_text, body.answer)
        except Exception:
            # Fall back: store the raw text — the engine treats unknowns gracefully.
            value = body.answer

    session_store.update_preferences(body.session_id, {body.question_key: value})
    session_store.record_answer(body.session_id, body.question_key)

    s = session_store.get_session(body.session_id)
    return {"next_question": _next_question(s)}


@app.post("/session/recommend")
def recommend(body: RecommendBody):
    s = session_store.get_session(body.session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"products": _run_recommendations(s)}


@app.post("/session/refine")
def refine(body: RefineBody):
    s = session_store.get_session(body.session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        result = claude_client.parse_supplement(body.text, s["preferences"], s["raw_input"])
    except Exception:
        # Without LLM access, treat the user's supplement as an acknowledged note
        # and re-run recommendations against the same preferences.
        result = {
            "preference_updates": {},
            "ai_response": f'Got it — "{body.text}". Updated recommendations below.',
        }
    session_store.update_preferences(body.session_id, result["preference_updates"])

    s = session_store.get_session(body.session_id)
    products = _run_recommendations(s)
    session_store.add_supplement_log(body.session_id, body.text, result["ai_response"])

    return {"products": products, "ai_response": result["ai_response"]}


# Lifecycle data for Scene 5 — keyed per category. Mock data so the
# post-purchase view always renders in the demo without requiring real
# integrations (calendar, smart home, etc.).
LIFECYCLE_DATA = {
    "smart_display": {
        "header": "Kitchen Display",
        "schedule": [
            {"time": "9:00 AM",  "label": "Soccer practice — Emma"},
            {"time": "2:00 PM",  "label": "Grocery delivery"},
            {"time": "6:00 PM",  "label": "Family dinner"},
        ],
        "menu": [
            {"meal": "Breakfast", "label": "Greek yogurt & granola"},
            {"meal": "Lunch",     "label": "Chicken salad wrap"},
            {"meal": "Dinner",    "label": "Teriyaki salmon bowl"},
        ],
        "video": {"title": "Cooking show: Quick weeknight meals",
                  "subtitle": "Watch while preparing dinner"},
        "cards": [
            {"icon": "🍴",  "title": "Meal Planning",
             "body": "Track nutrition, plan meals ahead, and generate shopping lists automatically."},
            {"icon": "👨‍👩‍👧", "title": "Family Hub",
             "body": "Sync schedules, leave messages, and coordinate family activities in one place."},
            {"icon": "🎬",  "title": "Entertainment",
             "body": "Watch cooking shows, follow video recipes, or enjoy music during meal prep."},
        ],
    },
    "water_bottle": {
        "header": "Daily Hydration",
        "schedule": [
            {"time": "7:00 AM",  "label": "Morning workout — 32oz before"},
            {"time": "12:30 PM", "label": "Refill at lunch"},
            {"time": "5:00 PM",  "label": "Evening run"},
        ],
        "menu": [
            {"meal": "Goal",      "label": "100 oz / day"},
            {"meal": "Reminder",  "label": "Sip every 20 minutes"},
            {"meal": "Tonight",   "label": "Lemon-mint infusion"},
        ],
        "video": {"title": "Workout reminder: Hydrate before, during, after",
                  "subtitle": "Coaching tips synced to your run"},
        "cards": [
            {"icon": "💧", "title": "Hydration Tracker",
             "body": "Log every refill; the assistant nudges you when you're falling behind your goal."},
            {"icon": "🏃", "title": "Workout Companion",
             "body": "Sync sessions and remind you to top up before, during, and after each workout."},
            {"icon": "🍋", "title": "Flavor Ideas",
             "body": "Rotate through citrus, herbal, and electrolyte recipes so plain water never gets boring."},
        ],
    },
    "kitchen_organizer": {
        "header": "Organized Kitchen",
        "schedule": [
            {"time": "Mon",  "label": "Pantry restock — check bins"},
            {"time": "Wed",  "label": "Wipe down lazy susan"},
            {"time": "Sat",  "label": "Weekly grocery run"},
        ],
        "menu": [
            {"meal": "Cabinet",   "label": "Stackable bins — clear"},
            {"meal": "Drawer",    "label": "Flatware tray — sorted"},
            {"meal": "Counter",   "label": "Spice lazy susan — visible"},
        ],
        "video": {"title": "Kitchen reset: 10-minute weekly tidy",
                  "subtitle": "A simple routine to keep everything findable"},
        "cards": [
            {"icon": "🗂️", "title": "Stay Organized",
             "body": "Get gentle weekly nudges to reset bins, drawers, and the lazy susan in 10 minutes."},
            {"icon": "🛒", "title": "Smart Restock",
             "body": "Track what's running low and feed it into your shopping list automatically."},
            {"icon": "✨", "title": "Calm Counters",
             "body": "Keep the everyday items visible and the rest tucked away — fewer decisions, faster cooking."},
        ],
    },
}


@app.get("/session/{session_id}/lifecycle")
def lifecycle(session_id: str):
    s = session_store.get_session(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    data = LIFECYCLE_DATA.get(s["category"], LIFECYCLE_DATA["smart_display"])
    return data
