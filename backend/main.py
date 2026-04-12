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
    }


def _run_recommendations(session: dict) -> list[dict]:
    products = engine.recommend_products(session["preferences"], top_n=5)
    explanations = claude_client.write_explanations(
        products, session["preferences"], session["raw_input"]
    )
    formatted = [_format_product(p, explanations[i]) for i, p in enumerate(products)]
    session_store.set_recommendations(session["session_id"], formatted)
    return formatted


# --- Routes ---

@app.post("/session/start")
def start_session(body: StartBody):
    parsed = claude_client.parse_initial_input(body.text)
    category = parsed.get("category", "unknown")
    preferences = parsed.get("preferences", {})

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
        value = claude_client.map_free_text_answer(body.question_key, question_text, body.answer)

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

    result = claude_client.parse_supplement(body.text, s["preferences"], s["raw_input"])
    session_store.update_preferences(body.session_id, result["preference_updates"])

    s = session_store.get_session(body.session_id)
    products = _run_recommendations(s)
    session_store.add_supplement_log(body.session_id, body.text, result["ai_response"])

    return {"products": products, "ai_response": result["ai_response"]}
