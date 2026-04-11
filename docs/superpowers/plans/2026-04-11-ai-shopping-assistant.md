# AI Shopping Assistant Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a FastAPI + React shopping assistant that takes a natural language description, asks up to 3 guided questions, and returns 5 product recommendations with Claude-written personal explanations.

**Architecture:** Claude parses free-text input into structured preferences; a fixed question sequence per category (max 3 questions, already-answered ones skipped) collects remaining unknowns; the existing `recommend_products()` engine scores and ranks products; Claude writes personal explanations for the top 5. A supplement bar at the bottom allows unlimited free-text refinement after results appear.

**Tech Stack:** Python 3.11+, FastAPI, Anthropic SDK (`anthropic`), pytest, React 18, Vite, plain CSS (no UI library)

---

### Task 1: Scaffold backend and frontend

**Files:**
- Create: `recommendation_Algorithem/explainability.py`
- Create: `backend/requirements.txt`
- Create: `frontend/` (Vite scaffold)

- [ ] **Step 1: Check if explainability.py exists**

```bash
ls /Users/sabrina/Projects/shopping-assistant-4/recommendation_Algorithem/
```

Expected: you see `recommendation_engine_refactored.py`. If `explainability.py` is NOT listed, create it in the next step. If it IS listed, skip step 2.

- [ ] **Step 2: Create explainability stub (if missing)**

```python
# recommendation_Algorithem/explainability.py
"""Stub — explanations are replaced by Claude-generated ones in the shopping assistant app."""

def generate_explanation(product, preferences, rule_matches=None, features=None):
    return ""
```

- [ ] **Step 3: Create backend requirements.txt**

```
# backend/requirements.txt
fastapi==0.115.5
uvicorn[standard]==0.32.1
anthropic==0.40.0
python-dotenv==1.0.1
pytest==8.3.3
httpx==0.27.2
```

- [ ] **Step 4: Install backend dependencies**

```bash
cd /Users/sabrina/Projects/shopping-assistant-4
python -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt
```

Expected: installs without errors.

- [ ] **Step 5: Create frontend with Vite**

```bash
cd /Users/sabrina/Projects/shopping-assistant-4
npm create vite@latest frontend -- --template react
cd frontend && npm install
```

Expected: `frontend/` directory exists with `src/App.jsx`, `package.json`.

- [ ] **Step 6: Verify the recommendation engine imports correctly**

```bash
cd /Users/sabrina/Projects/shopping-assistant-4
source backend/.venv/bin/activate
python -c "
import sys
from pathlib import Path
sys.path.insert(0, 'recommendation_Algorithem')
import recommendation_engine_refactored as engine
engine.DATA_PATH = Path('data/clean/products_clean.json')
results = engine.recommend_products({'category': 'water_bottle', 'priority': 'balanced'}, top_n=3)
print(f'OK — got {len(results)} results')
print(results[0]['title'])
"
```

Expected: prints `OK — got 3 results` and a product title.

- [ ] **Step 7: Create backend tests directory**

```bash
mkdir -p /Users/sabrina/Projects/shopping-assistant-4/backend/tests
touch /Users/sabrina/Projects/shopping-assistant-4/backend/tests/__init__.py
```

- [ ] **Step 8: Commit**

```bash
cd /Users/sabrina/Projects/shopping-assistant-4
git init  # only if not already a git repo
git add recommendation_Algorithem/explainability.py backend/requirements.txt frontend/
git commit -m "chore: scaffold backend requirements and frontend vite app"
```

---

### Task 2: Question definitions module

**Files:**
- Create: `backend/questions.py`
- Create: `backend/tests/test_questions.py`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_questions.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from questions import get_question_queue, get_question, CHIP_TO_VALUE, CATEGORY_ALIASES


def test_all_unanswered_questions_returned():
    prefs = {"use_area": None, "pain_point": None, "structure_type": None}
    queue = get_question_queue("kitchen_organizer", prefs)
    assert queue == ["use_area", "pain_point", "structure_type"]


def test_answered_questions_skipped():
    prefs = {"use_area": "cabinet", "pain_point": None, "structure_type": None}
    queue = get_question_queue("kitchen_organizer", prefs)
    assert queue == ["pain_point", "structure_type"]


def test_all_answered_returns_empty():
    prefs = {"use_area": "cabinet", "pain_point": "not_enough_space", "structure_type": "stackable"}
    queue = get_question_queue("kitchen_organizer", prefs)
    assert queue == []


def test_get_question_returns_correct_definition():
    q = get_question("water_bottle", "use_case")
    assert q["key"] == "use_case"
    assert "Gym" in q["chips"]


def test_get_question_returns_none_for_unknown_key():
    assert get_question("water_bottle", "nonexistent") is None


def test_chip_to_value_maps_correctly():
    assert CHIP_TO_VALUE["use_area"]["Cabinets"] == "cabinet"
    assert CHIP_TO_VALUE["insulated"]["Yes, insulated"] is True
    assert CHIP_TO_VALUE["price_max"]["Under $50"] == 50
    assert CHIP_TO_VALUE["delivery_days_max"]["No rush"] is None


def test_category_aliases_map_all_three():
    assert CATEGORY_ALIASES["Water Bottle"] == "water_bottle"
    assert CATEGORY_ALIASES["Smart Display"] == "smart_display"
    assert CATEGORY_ALIASES["Kitchen Organizer"] == "kitchen_organizer"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /Users/sabrina/Projects/shopping-assistant-4
source backend/.venv/bin/activate
pytest backend/tests/test_questions.py -v
```

Expected: `ModuleNotFoundError: No module named 'questions'`

- [ ] **Step 3: Create questions.py**

```python
# backend/questions.py
from typing import TypedDict, Any


class Question(TypedDict):
    key: str
    text: str
    chips: list[str]


QUESTION_SEQUENCES: dict[str, list[Question]] = {
    "kitchen_organizer": [
        {
            "key": "use_area",
            "text": "Where's the main problem area in your kitchen?",
            "chips": ["Cabinets", "Countertop", "Under the sink"],
        },
        {
            "key": "pain_point",
            "text": "What's your biggest frustration?",
            "chips": ["Not enough space", "Hard to find things"],
        },
        {
            "key": "structure_type",
            "text": "Any preference on the type of organizer?",
            "chips": ["Stackable", "Drawer", "Bin", "Expandable", "Lazy Susan"],
        },
    ],
    "water_bottle": [
        {
            "key": "use_case",
            "text": "What will you mainly use it for?",
            "chips": ["Gym", "Daily carry", "Outdoor", "Kids"],
        },
        {
            "key": "insulated",
            "text": "Do you need it to keep drinks hot or cold?",
            "chips": ["Yes, insulated", "No, doesn't matter"],
        },
        {
            "key": "size_preference",
            "text": "Any size preference?",
            "chips": ["Lightweight", "Large capacity", "No preference"],
        },
    ],
    "smart_display": [
        {
            "key": "use_case",
            "text": "What's the main thing you'll use it for?",
            "chips": ["Cooking", "Family calendar", "Entertainment", "Smart home control"],
        },
        {
            "key": "price_max",
            "text": "What's your budget?",
            "chips": ["Under $50", "Under $100", "Under $150", "No limit"],
        },
        {
            "key": "delivery_days_max",
            "text": "How soon do you need it?",
            "chips": ["ASAP (1–2 days)", "This week", "No rush"],
        },
    ],
}

CATEGORY_CHIPS = ["Water Bottle", "Smart Display", "Kitchen Organizer"]

CATEGORY_ALIASES: dict[str, str] = {
    "Water Bottle": "water_bottle",
    "Smart Display": "smart_display",
    "Kitchen Organizer": "kitchen_organizer",
}

# Maps chip display label → structured preference value
CHIP_TO_VALUE: dict[str, dict[str, Any]] = {
    "use_area": {
        "Cabinets": "cabinet",
        "Countertop": "countertop",
        "Under the sink": "under_sink",
    },
    "pain_point": {
        "Not enough space": "not_enough_space",
        "Hard to find things": "hard_to_find_things",
    },
    "structure_type": {
        "Stackable": "stackable",
        "Drawer": "drawer",
        "Bin": "bin",
        "Expandable": "expandable",
        "Lazy Susan": "lazy_susan",
    },
    "use_case": {
        "Gym": "gym",
        "Daily carry": "daily",
        "Outdoor": "outdoor",
        "Kids": "kids",
        "Cooking": "cooking",
        "Family calendar": "family",
        "Entertainment": "entertainment",
        "Smart home control": "smart_home",
    },
    "insulated": {
        "Yes, insulated": True,
        "No, doesn't matter": False,
    },
    "size_preference": {
        "Lightweight": "lightweight",
        "Large capacity": "large",
        "No preference": "",
    },
    "price_max": {
        "Under $50": 50,
        "Under $100": 100,
        "Under $150": 150,
        "No limit": None,
    },
    "delivery_days_max": {
        "ASAP (1–2 days)": 2,
        "This week": 7,
        "No rush": None,
    },
}


def get_question_queue(category: str, preferences: dict) -> list[str]:
    """Return question keys not yet answered (value is None)."""
    questions = QUESTION_SEQUENCES.get(category, [])
    return [q["key"] for q in questions if preferences.get(q["key"]) is None]


def get_question(category: str, key: str) -> Question | None:
    """Return the question definition for a given category and key."""
    questions = QUESTION_SEQUENCES.get(category, [])
    return next((q for q in questions if q["key"] == key), None)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest backend/tests/test_questions.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/questions.py backend/tests/test_questions.py
git commit -m "feat: question sequences and chip-to-value maps per category"
```

---

### Task 3: In-memory session store

**Files:**
- Create: `backend/session.py`
- Create: `backend/tests/test_session.py`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_session.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import session as session_module
from session import (
    create_session, get_session, update_preferences,
    update_category, record_answer, set_recommendations, add_supplement_log,
)


def setup_function():
    session_module._sessions.clear()


def test_create_session_returns_session_with_id():
    s = create_session("gym water bottle", "water_bottle", {"use_case": None})
    assert s["session_id"]
    assert s["category"] == "water_bottle"
    assert s["raw_input"] == "gym water bottle"


def test_get_session_returns_created_session():
    s = create_session("test", "water_bottle", {})
    retrieved = get_session(s["session_id"])
    assert retrieved["session_id"] == s["session_id"]


def test_get_session_returns_none_for_unknown():
    assert get_session("no-such-id") is None


def test_update_preferences_merges_values():
    s = create_session("test", "water_bottle", {"use_case": None, "insulated": None})
    update_preferences(s["session_id"], {"use_case": "gym"})
    updated = get_session(s["session_id"])
    assert updated["preferences"]["use_case"] == "gym"
    assert updated["preferences"]["insulated"] is None  # untouched


def test_update_category_sets_category():
    s = create_session("test", "", {})
    update_category(s["session_id"], "smart_display")
    assert get_session(s["session_id"])["category"] == "smart_display"


def test_record_answer_appends_key():
    s = create_session("test", "water_bottle", {})
    record_answer(s["session_id"], "use_case")
    assert "use_case" in get_session(s["session_id"])["answered"]


def test_record_answer_no_duplicates():
    s = create_session("test", "water_bottle", {})
    record_answer(s["session_id"], "use_case")
    record_answer(s["session_id"], "use_case")
    assert get_session(s["session_id"])["answered"].count("use_case") == 1


def test_set_recommendations_stores_list():
    s = create_session("test", "water_bottle", {})
    set_recommendations(s["session_id"], [{"title": "Bottle A"}])
    assert get_session(s["session_id"])["recommendations"][0]["title"] == "Bottle A"


def test_add_supplement_log_appends_entry():
    s = create_session("test", "water_bottle", {})
    add_supplement_log(s["session_id"], "under $20", "Got it, filtering to under $20.")
    log = get_session(s["session_id"])["supplement_log"]
    assert len(log) == 1
    assert log[0]["user_text"] == "under $20"
    assert log[0]["ai_response"] == "Got it, filtering to under $20."
    assert "timestamp" in log[0]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest backend/tests/test_session.py -v
```

Expected: `ModuleNotFoundError: No module named 'session'`

- [ ] **Step 3: Create session.py**

```python
# backend/session.py
import uuid
from datetime import datetime, timezone
from typing import Any

_sessions: dict[str, dict[str, Any]] = {}


def create_session(raw_input: str, category: str, preferences: dict) -> dict:
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "raw_input": raw_input,
        "category": category,
        "preferences": preferences,
        "answered": [],
        "recommendations": [],
        "supplement_log": [],
    }
    _sessions[session_id] = session
    return session


def get_session(session_id: str) -> dict | None:
    return _sessions.get(session_id)


def update_preferences(session_id: str, updates: dict) -> None:
    _sessions[session_id]["preferences"].update(updates)


def update_category(session_id: str, category: str) -> None:
    _sessions[session_id]["category"] = category


def record_answer(session_id: str, question_key: str) -> None:
    answered = _sessions[session_id]["answered"]
    if question_key not in answered:
        answered.append(question_key)


def set_recommendations(session_id: str, recommendations: list) -> None:
    _sessions[session_id]["recommendations"] = recommendations


def add_supplement_log(session_id: str, user_text: str, ai_response: str) -> None:
    _sessions[session_id]["supplement_log"].append({
        "user_text": user_text,
        "ai_response": ai_response,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest backend/tests/test_session.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/session.py backend/tests/test_session.py
git commit -m "feat: in-memory session store with full CRUD operations"
```

---

### Task 4: Claude client (4 call sites)

**Files:**
- Create: `backend/claude_client.py`
- Create: `backend/tests/test_claude_client.py`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_claude_client.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from unittest.mock import MagicMock, patch


def _mock_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=content)]
    return msg


@patch("claude_client.client")
def test_parse_initial_input_extracts_category_and_preferences(mock_client):
    from claude_client import parse_initial_input
    mock_client.messages.create.return_value = _mock_response(json.dumps({
        "category": "water_bottle",
        "preferences": {
            "use_case": "gym", "insulated": True, "size_preference": None,
            "pain_point": None, "use_area": None, "structure_type": None,
            "price_max": None, "delivery_days_max": None, "priority": "balanced",
        },
    }))
    result = parse_initial_input("I need a water bottle for the gym")
    assert result["category"] == "water_bottle"
    assert result["preferences"]["use_case"] == "gym"
    assert result["preferences"]["insulated"] is True


@patch("claude_client.client")
def test_parse_initial_input_handles_markdown_fences(mock_client):
    from claude_client import parse_initial_input
    mock_client.messages.create.return_value = _mock_response(
        "```json\n" + json.dumps({"category": "smart_display", "preferences": {}}) + "\n```"
    )
    result = parse_initial_input("smart display for cooking")
    assert result["category"] == "smart_display"


@patch("claude_client.client")
def test_map_free_text_answer_returns_structured_value(mock_client):
    from claude_client import map_free_text_answer
    mock_client.messages.create.return_value = _mock_response('"gym"')
    result = map_free_text_answer("use_case", "What will you use it for?", "I go running every morning")
    assert result == "gym"


@patch("claude_client.client")
def test_write_explanations_returns_five_strings(mock_client):
    from claude_client import write_explanations
    mock_client.messages.create.return_value = _mock_response(
        json.dumps(["Exp 1", "Exp 2", "Exp 3", "Exp 4", "Exp 5"])
    )
    products = [{"title": f"Product {i}", "price": 20.0, "rating": 4.5} for i in range(5)]
    result = write_explanations(products, {"use_case": "gym"}, "water bottle for gym")
    assert len(result) == 5
    assert all(isinstance(e, str) for e in result)


@patch("claude_client.client")
def test_parse_supplement_returns_updates_and_response(mock_client):
    from claude_client import parse_supplement
    mock_client.messages.create.return_value = _mock_response(json.dumps({
        "preference_updates": {"price_max": 20},
        "ai_response": "Got it — filtering to under $20.",
    }))
    result = parse_supplement("make it under $20", {"use_case": "gym"}, "water bottle")
    assert result["preference_updates"]["price_max"] == 20
    assert "20" in result["ai_response"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest backend/tests/test_claude_client.py -v
```

Expected: `ModuleNotFoundError: No module named 'claude_client'`

- [ ] **Step 3: Create claude_client.py**

```python
# backend/claude_client.py
import json
import os
import anthropic

MODEL = "claude-opus-4-6"
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

_PARSE_SYSTEM = """\
You are a shopping assistant. Extract structured shopping intent from user input.
Return ONLY a JSON object with this exact shape:
{"category": "kitchen_organizer|water_bottle|smart_display|unknown",
 "preferences": {"use_area": null, "pain_point": null, "structure_type": null,
                 "use_case": null, "insulated": null, "size_preference": null,
                 "price_max": null, "delivery_days_max": null, "priority": "balanced"}}
Fill in any preference you can confidently infer. Leave others null.
price_max must be a number or null. delivery_days_max must be a number or null.
insulated must be true, false, or null. Set category to "unknown" if not confident.\
"""

_EXPLAIN_SYSTEM = """\
You are a personal shopping assistant. Write a short (1–2 sentences) personal explanation
for why each product fits this specific customer. Use their actual words and context.
Be specific, not generic.
Return ONLY a JSON array of 5 strings, one per product.
Example: ["Perfect for gym sessions — insulated to keep drinks cold for hours.", ...]\
"""

_SUPPLEMENT_SYSTEM = """\
You are a personal shopping assistant. Extract any preference updates from the user's message
and write a short (1–2 sentences) conversational acknowledgement.
Return ONLY a JSON object:
{"preference_updates": {"key": value}, "ai_response": "..."}
Only include keys the user explicitly changed.
price_max and delivery_days_max must be numbers or null. insulated must be true, false, or null.\
"""


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        parts = text.split("```")
        text = parts[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def parse_initial_input(text: str) -> dict:
    """Extract category and preferences from raw user text. Returns {category, preferences}."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=_PARSE_SYSTEM,
        messages=[{"role": "user", "content": text}],
    )
    return json.loads(_strip_fences(resp.content[0].text))


def map_free_text_answer(question_key: str, question_text: str, answer_text: str):
    """Map a free-text answer to its structured preference value."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=128,
        system=(
            f"Map the user's answer to a structured value for: '{question_text}' (key: {question_key}).\n"
            "Return ONLY a JSON value — string, number, boolean, or null. No explanation.\n"
            "Examples: 'I go running' → \"gym\" | 'keep drinks cold' → true | 'around $25' → 25"
        ),
        messages=[{"role": "user", "content": answer_text}],
    )
    return json.loads(_strip_fences(resp.content[0].text))


def write_explanations(products: list[dict], preferences: dict, raw_input: str) -> list[str]:
    """Write one personal explanation per product. Returns list of 5 strings."""
    summaries = "\n".join(
        f"{i+1}. {p['title']} — ${p['price']}, {p.get('rating', 'N/A')}★"
        for i, p in enumerate(products)
    )
    filled = {k: v for k, v in preferences.items() if v is not None}
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=_EXPLAIN_SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                f'Customer said: "{raw_input}"\n'
                f"Their preferences: {json.dumps(filled)}\n\n"
                f"Products:\n{summaries}"
            ),
        }],
    )
    return json.loads(_strip_fences(resp.content[0].text))


def parse_supplement(text: str, preferences: dict, raw_input: str) -> dict:
    """Extract preference deltas + write AI response. Returns {preference_updates, ai_response}."""
    filled = {k: v for k, v in preferences.items() if v is not None}
    resp = client.messages.create(
        model=MODEL,
        max_tokens=512,
        system=_SUPPLEMENT_SYSTEM,
        messages=[{
            "role": "user",
            "content": (
                f'Original request: "{raw_input}"\n'
                f"Current preferences: {json.dumps(filled)}\n\n"
                f'User says: "{text}"'
            ),
        }],
    )
    return json.loads(_strip_fences(resp.content[0].text))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest backend/tests/test_claude_client.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/claude_client.py backend/tests/test_claude_client.py
git commit -m "feat: Claude client with 4 call sites (parse, map, explain, supplement)"
```

---

### Task 5: FastAPI routes

**Files:**
- Create: `backend/main.py`

- [ ] **Step 1: Create main.py**

```python
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
```

- [ ] **Step 2: Verify the app starts**

```bash
cd /Users/sabrina/Projects/shopping-assistant-4/backend
source .venv/bin/activate
ANTHROPIC_API_KEY=placeholder uvicorn main:app --reload --port 8000
```

Expected: `Application startup complete.` (Ctrl+C to stop)

- [ ] **Step 3: Commit**

```bash
git add backend/main.py
git commit -m "feat: FastAPI routes for start, answer, recommend, refine"
```

---

### Task 6: Backend integration tests

**Files:**
- Create: `backend/tests/test_routes.py`

- [ ] **Step 1: Write the failing tests**

```python
# backend/tests/test_routes.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

import session as session_module


@pytest.fixture(autouse=True)
def clear_sessions():
    session_module._sessions.clear()
    yield
    session_module._sessions.clear()


def _mock_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = [MagicMock(text=content)]
    return msg


def _mock_products(n: int = 5) -> list[dict]:
    return [
        {
            "title": f"Product {i}",
            "price": 20.0,
            "rating": 4.5,
            "image_url": "https://example.com/img.jpg",
            "product_url": "https://example.com/product",
            "category": "water_bottle",
            "arrival_time_days": 3,
        }
        for i in range(n)
    ]


@patch("claude_client.client")
@patch("main.engine")
def test_start_known_category_returns_first_question(mock_engine, mock_claude):
    from main import app
    client = TestClient(app)

    mock_claude.messages.create.return_value = _mock_response(json.dumps({
        "category": "water_bottle",
        "preferences": {
            "use_case": None, "insulated": None, "size_preference": None,
            "pain_point": None, "use_area": None, "structure_type": None,
            "price_max": None, "delivery_days_max": None, "priority": "balanced",
        },
    }))

    resp = client.post("/session/start", json={"text": "I need a water bottle"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] == "water_bottle"
    assert data["session_id"]
    assert data["next_question"]["key"] == "use_case"
    assert "Gym" in data["next_question"]["chips"]
    assert data["chips"] is None


@patch("claude_client.client")
@patch("main.engine")
def test_start_unknown_category_returns_chips(mock_engine, mock_claude):
    from main import app
    client = TestClient(app)

    mock_claude.messages.create.return_value = _mock_response(json.dumps({
        "category": "unknown",
        "preferences": {
            "use_case": None, "insulated": None, "size_preference": None,
            "pain_point": None, "use_area": None, "structure_type": None,
            "price_max": None, "delivery_days_max": None, "priority": "balanced",
        },
    }))

    resp = client.post("/session/start", json={"text": "something nice"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["category"] is None
    assert "Water Bottle" in data["chips"]
    assert data["next_question"] is None


@patch("claude_client.client")
@patch("main.engine")
def test_answer_chip_advances_to_next_question(mock_engine, mock_claude):
    from main import app
    client = TestClient(app)

    # Start session
    mock_claude.messages.create.return_value = _mock_response(json.dumps({
        "category": "water_bottle",
        "preferences": {
            "use_case": None, "insulated": None, "size_preference": None,
            "pain_point": None, "use_area": None, "structure_type": None,
            "price_max": None, "delivery_days_max": None, "priority": "balanced",
        },
    }))
    start = client.post("/session/start", json={"text": "water bottle"}).json()
    sid = start["session_id"]

    # Answer use_case with chip
    resp = client.post("/session/answer", json={
        "session_id": sid,
        "question_key": "use_case",
        "answer": "Gym",
        "is_chip": True,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["next_question"]["key"] == "insulated"


@patch("claude_client.client")
@patch("main.engine")
def test_recommend_returns_five_products(mock_engine, mock_claude):
    from main import app
    client = TestClient(app)

    # Start session with all preferences already filled
    mock_claude.messages.create.return_value = _mock_response(json.dumps({
        "category": "water_bottle",
        "preferences": {
            "use_case": "gym", "insulated": True, "size_preference": "lightweight",
            "pain_point": None, "use_area": None, "structure_type": None,
            "price_max": None, "delivery_days_max": None, "priority": "balanced",
        },
    }))
    start = client.post("/session/start", json={"text": "gym water bottle"}).json()
    sid = start["session_id"]

    # Mock engine and explanations
    mock_engine.recommend_products.return_value = _mock_products(5)
    mock_claude.messages.create.return_value = _mock_response(
        json.dumps(["Exp 1", "Exp 2", "Exp 3", "Exp 4", "Exp 5"])
    )

    resp = client.post("/session/recommend", json={"session_id": sid})
    assert resp.status_code == 200
    products = resp.json()["products"]
    assert len(products) == 5
    assert products[0]["explanation"] == "Exp 1"


@patch("claude_client.client")
@patch("main.engine")
def test_refine_updates_preferences_and_returns_new_products(mock_engine, mock_claude):
    from main import app
    client = TestClient(app)

    mock_claude.messages.create.return_value = _mock_response(json.dumps({
        "category": "water_bottle",
        "preferences": {
            "use_case": "gym", "insulated": True, "size_preference": "lightweight",
            "pain_point": None, "use_area": None, "structure_type": None,
            "price_max": None, "delivery_days_max": None, "priority": "balanced",
        },
    }))
    start = client.post("/session/start", json={"text": "gym water bottle"}).json()
    sid = start["session_id"]

    mock_engine.recommend_products.return_value = _mock_products(5)
    mock_claude.messages.create.return_value = _mock_response(json.dumps({
        "preference_updates": {"price_max": 20},
        "ai_response": "Got it — showing options under $20.",
    }))
    # Second call for explanations
    mock_claude.messages.create.side_effect = [
        _mock_response(json.dumps({"preference_updates": {"price_max": 20}, "ai_response": "Got it."})),
        _mock_response(json.dumps(["Exp 1", "Exp 2", "Exp 3", "Exp 4", "Exp 5"])),
    ]

    resp = client.post("/session/refine", json={"session_id": sid, "text": "under $20"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_response"] == "Got it."
    assert len(data["products"]) == 5

    updated = session_module.get_session(sid)
    assert updated["preferences"]["price_max"] == 20
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest backend/tests/test_routes.py -v
```

Expected: import errors or failures because routes aren't wired yet (if main.py was just created, they may pass — that's fine, move to step 3).

- [ ] **Step 3: Run all backend tests together**

```bash
pytest backend/tests/ -v
```

Expected: all tests PASS. If any fail, fix them before proceeding.

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_routes.py
git commit -m "test: backend integration tests for all four API routes"
```

---

### Task 7: Frontend global styles and App shell

**Files:**
- Modify: `frontend/src/main.jsx`
- Modify: `frontend/src/App.jsx`
- Create: `frontend/src/App.css`

- [ ] **Step 1: Replace main.jsx**

```jsx
// frontend/src/main.jsx
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './App.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
```

- [ ] **Step 2: Create App.css**

```css
/* frontend/src/App.css */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --accent-start: #6c63ff;
  --accent-end: #a855f7;
  --accent-gradient: linear-gradient(90deg, #6c63ff, #a855f7);
  --bg-gradient: linear-gradient(135deg, #f0f4ff 0%, #faf0ff 100%);
  --text-primary: #1a1a2e;
  --text-secondary: #9ca3af;
  --card-bg: #ffffff;
  --chip-border: #e0deff;
  --chip-text: #6c63ff;
  --nav-bg: rgba(255, 255, 255, 0.8);
  --shadow-card: 0 2px 16px rgba(108, 99, 255, 0.08);
  --shadow-icon: 0 4px 16px rgba(108, 99, 255, 0.35);
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--bg-gradient);
  min-height: 100vh;
  color: var(--text-primary);
}

nav {
  background: var(--nav-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(120, 100, 200, 0.1);
  padding: 12px 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
}

nav .logo {
  font-size: 15px;
  font-weight: 700;
  background: var(--accent-gradient);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

nav .subtitle {
  font-size: 12px;
  color: var(--text-secondary);
}

.page {
  max-width: 680px;
  margin: 0 auto;
  padding: 48px 24px 120px;
}

/* Hero icon */
.hero-icon {
  width: 64px;
  height: 64px;
  background: var(--accent-gradient);
  border-radius: 18px;
  box-shadow: var(--shadow-icon);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
}

/* Buttons */
.btn-primary {
  background: var(--accent-gradient);
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 12px 28px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.15s, transform 0.1s;
  box-shadow: 0 2px 12px rgba(108, 99, 255, 0.3);
}
.btn-primary:hover { opacity: 0.92; transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

.btn-ghost {
  background: transparent;
  border: none;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: 6px;
}
.btn-ghost:hover { background: rgba(108, 99, 255, 0.06); color: var(--chip-text); }

/* Chips */
.chip {
  border: 1.5px solid var(--chip-border);
  border-radius: 24px;
  padding: 8px 18px;
  font-size: 14px;
  color: var(--chip-text);
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
  font-weight: 500;
}
.chip:hover { border-color: var(--accent-start); background: rgba(108, 99, 255, 0.04); }
.chip.selected {
  background: var(--accent-gradient);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 2px 10px rgba(108, 99, 255, 0.3);
}

/* Cards */
.card {
  background: var(--card-bg);
  border-radius: 14px;
  box-shadow: var(--shadow-card);
  overflow: hidden;
}

/* Progress bar */
.progress-bar {
  height: 4px;
  background: rgba(108, 99, 255, 0.12);
  border-radius: 2px;
  overflow: hidden;
}
.progress-bar-fill {
  height: 100%;
  background: var(--accent-gradient);
  border-radius: 2px;
  transition: width 0.35s ease;
}

/* Loading dots */
.loading-dots span {
  display: inline-block;
  width: 6px;
  height: 6px;
  margin: 0 2px;
  background: var(--accent-start);
  border-radius: 50%;
  animation: dot-bounce 1.2s infinite;
}
.loading-dots span:nth-child(2) { animation-delay: 0.2s; }
.loading-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes dot-bounce {
  0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
  40% { transform: translateY(-6px); opacity: 1; }
}

/* Textarea */
textarea {
  width: 100%;
  border: 1.5px solid var(--chip-border);
  border-radius: 10px;
  padding: 14px 16px;
  font-size: 15px;
  color: var(--text-primary);
  background: #fff;
  resize: none;
  outline: none;
  font-family: inherit;
  line-height: 1.5;
  transition: border-color 0.15s;
}
textarea:focus { border-color: var(--accent-start); }
textarea::placeholder { color: var(--text-secondary); }

/* Supplement bar */
.supplement-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: var(--nav-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-top: 1px solid rgba(120, 100, 200, 0.12);
  padding: 12px 24px;
  z-index: 100;
}
```

- [ ] **Step 3: Create App.jsx shell**

```jsx
// frontend/src/App.jsx
import { useState } from 'react'
import Stage1 from './components/Stage1'
import Stage2 from './components/Stage2'
import Stage3 from './components/Stage3'

export default function App() {
  const [stage, setStage] = useState(1)
  const [sessionId, setSessionId] = useState(null)
  const [products, setProducts] = useState([])
  const [supplementLog, setSupplementLog] = useState([])

  // Data from /session/start — carries pending question or category chips
  const [startData, setStartData] = useState(null)

  const handleStage1Complete = (data) => {
    setSessionId(data.session_id)
    setStartData(data)
    setStage(2)
  }

  const handleStage2Complete = (fetchedProducts) => {
    setProducts(fetchedProducts)
    setStage(3)
  }

  const handleSupplement = (fetchedProducts, aiResponse) => {
    setProducts(fetchedProducts)
    setSupplementLog((prev) => [{ aiResponse, timestamp: Date.now() }, ...prev])
  }

  return (
    <>
      <nav>
        <span className="logo">ShopSmart</span>
        <span className="subtitle">AI Assistant</span>
      </nav>
      <div className="page">
        {stage === 1 && <Stage1 onComplete={handleStage1Complete} />}
        {stage === 2 && (
          <Stage2
            sessionId={sessionId}
            startData={startData}
            onComplete={handleStage2Complete}
          />
        )}
        {stage === 3 && (
          <Stage3
            sessionId={sessionId}
            products={products}
            supplementLog={supplementLog}
            onSupplement={handleSupplement}
          />
        )}
      </div>
    </>
  )
}
```

- [ ] **Step 4: Start dev server and verify it loads**

```bash
cd /Users/sabrina/Projects/shopping-assistant-4/frontend
npm run dev
```

Open `http://localhost:5173` — should show nav bar and a blank page (Stage1 not yet built). No console errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/main.jsx frontend/src/App.jsx frontend/src/App.css
git commit -m "feat: app shell with stage routing and global CSS design system"
```

---

### Task 8: API client

**Files:**
- Create: `frontend/src/api.js`

- [ ] **Step 1: Create api.js**

```js
// frontend/src/api.js
const BASE = 'http://localhost:8000'

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

export const startSession = (text) => post('/session/start', { text })

export const answerQuestion = (sessionId, questionKey, answer, isChip = false) =>
  post('/session/answer', {
    session_id: sessionId,
    question_key: questionKey,
    answer,
    is_chip: isChip,
  })

export const getRecommendations = (sessionId) =>
  post('/session/recommend', { session_id: sessionId })

export const refineRecommendations = (sessionId, text) =>
  post('/session/refine', { session_id: sessionId, text })
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api.js
git commit -m "feat: API client module for all four backend endpoints"
```

---

### Task 9: Stage 1 — landing page

**Files:**
- Create: `frontend/src/components/Stage1.jsx`

- [ ] **Step 1: Create Stage1.jsx**

```jsx
// frontend/src/components/Stage1.jsx
import { useState } from 'react'
import { startSession } from '../api'

function LoadingDots() {
  return (
    <span className="loading-dots">
      <span /><span /><span />
    </span>
  )
}

export default function Stage1({ onComplete }) {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async () => {
    if (!text.trim() || loading) return
    setLoading(true)
    setError(null)
    try {
      const data = await startSession(text.trim())
      onComplete(data)
    } catch (e) {
      setError('Something went wrong. Please try again.')
      setLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) handleSubmit()
  }

  return (
    <div style={{ textAlign: 'center', paddingTop: 32 }}>
      {/* Shopping bag icon */}
      <div className="hero-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none"
          stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M6 2L3 6v14a2 2 0 002 2h14a2 2 0 002-2V6l-3-4z" />
          <line x1="3" y1="6" x2="21" y2="6" />
          <path d="M16 10a4 4 0 01-8 0" />
        </svg>
      </div>

      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 12 }}>
        AI Shopping Assistant
      </h1>
      <p style={{ color: 'var(--text-secondary)', fontSize: 16, marginBottom: 32, lineHeight: 1.6 }}>
        Tell me what you need, what matters to you,<br />
        or what problem you're trying to solve
      </p>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="I need a water bottle for the gym..."
        rows={4}
        style={{ marginBottom: 16 }}
        autoFocus
      />

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
        <button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={!text.trim() || loading}
        >
          {loading ? <LoadingDots /> : 'Find my matches →'}
        </button>
        <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
          ⌘ + Enter to submit
        </span>
      </div>

      {error && (
        <p style={{ color: '#ef4444', marginTop: 16, fontSize: 14 }}>{error}</p>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Verify Stage 1 renders correctly in the browser**

With the dev server running (`npm run dev`), open `http://localhost:5173`. You should see:
- Gradient background
- Shopping bag icon in a purple badge
- Title and subtitle text
- Textarea with placeholder
- "Find my matches →" button (disabled until text typed)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Stage1.jsx
git commit -m "feat: Stage 1 landing page with hero icon and text input"
```

---

### Task 10: Stage 2 — guided questions

**Files:**
- Create: `frontend/src/components/Stage2.jsx`

- [ ] **Step 1: Create Stage2.jsx**

```jsx
// frontend/src/components/Stage2.jsx
import { useState, useEffect } from 'react'
import { answerQuestion, getRecommendations } from '../api'
import { CATEGORY_CHIPS } from '../constants'

// Number of total questions per category (used for progress bar)
const TOTAL_QUESTIONS = { kitchen_organizer: 3, water_bottle: 3, smart_display: 3 }

function LoadingDots() {
  return <span className="loading-dots"><span /><span /><span /></span>
}

export default function Stage2({ sessionId, startData, onComplete }) {
  const [currentQuestion, setCurrentQuestion] = useState(
    startData.next_question || null
  )
  const [showCategoryChips, setShowCategoryChips] = useState(
    !!startData.chips
  )
  const [category, setCategory] = useState(startData.category)
  const [stepIndex, setStepIndex] = useState(0)
  const [totalSteps, setTotalSteps] = useState(
    startData.category ? TOTAL_QUESTIONS[startData.category] || 3 : 3
  )
  const [freeText, setFreeText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  // If no questions at all (all inferred), fetch recommendations immediately
  useEffect(() => {
    if (!showCategoryChips && !currentQuestion) {
      fetchRecommendations()
    }
  }, [])

  const fetchRecommendations = async () => {
    setLoading(true)
    try {
      const data = await getRecommendations(sessionId)
      onComplete(data.products)
    } catch (e) {
      setError('Could not load recommendations. Please try again.')
      setLoading(false)
    }
  }

  const handleChipAnswer = async (questionKey, chipLabel, isCategory = false) => {
    setLoading(true)
    setError(null)
    try {
      const data = await answerQuestion(sessionId, questionKey, chipLabel, true)
      if (isCategory) {
        setShowCategoryChips(false)
        setCategory(chipLabel.toLowerCase().replace(' ', '_'))
      }
      if (data.next_question) {
        setCurrentQuestion(data.next_question)
        setStepIndex((i) => i + 1)
      } else {
        await fetchRecommendations()
      }
    } catch (e) {
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleFreeTextSubmit = async () => {
    if (!freeText.trim() || loading) return
    setLoading(true)
    setError(null)
    try {
      const data = await answerQuestion(sessionId, currentQuestion.key, freeText.trim(), false)
      setFreeText('')
      if (data.next_question) {
        setCurrentQuestion(data.next_question)
        setStepIndex((i) => i + 1)
      } else {
        await fetchRecommendations()
      }
    } catch (e) {
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSkip = async () => {
    setLoading(true)
    setError(null)
    try {
      // Skip by answering with empty string as a chip (no Claude call)
      const data = await answerQuestion(sessionId, currentQuestion.key, '', true)
      if (data.next_question) {
        setCurrentQuestion(data.next_question)
        setStepIndex((i) => i + 1)
      } else {
        await fetchRecommendations()
      }
    } catch (e) {
      setError('Something went wrong.')
    } finally {
      setLoading(false)
    }
  }

  const progressPct = totalSteps > 0 ? Math.round(((stepIndex) / totalSteps) * 100) : 0

  if (loading && !currentQuestion && !showCategoryChips) {
    return (
      <div style={{ textAlign: 'center', paddingTop: 64 }}>
        <p style={{ color: 'var(--text-secondary)', marginBottom: 16 }}>
          Finding your matches...
        </p>
        <LoadingDots />
      </div>
    )
  }

  return (
    <div style={{ maxWidth: 480, margin: '0 auto', paddingTop: 16 }}>
      {/* Progress bar (hidden during category selection) */}
      {!showCategoryChips && (
        <div style={{ marginBottom: 32 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
              Step {stepIndex + 1} of {totalSteps}
            </span>
          </div>
          <div className="progress-bar">
            <div className="progress-bar-fill" style={{ width: `${progressPct}%` }} />
          </div>
        </div>
      )}

      {/* Category chip selection (when category unknown) */}
      {showCategoryChips && (
        <div style={{ textAlign: 'center' }}>
          <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>
            What are you shopping for?
          </h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: 28, fontSize: 15 }}>
            Help me point you in the right direction
          </p>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, justifyContent: 'center' }}>
            {['Water Bottle', 'Smart Display', 'Kitchen Organizer'].map((label) => (
              <button
                key={label}
                className="chip"
                onClick={() => handleChipAnswer('category', label, true)}
                disabled={loading}
              >
                {label}
              </button>
            ))}
          </div>
          {loading && <div style={{ marginTop: 20 }}><LoadingDots /></div>}
        </div>
      )}

      {/* Guided question */}
      {!showCategoryChips && currentQuestion && (
        <div>
          <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 8 }}>
            {currentQuestion.text}
          </h2>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 24, marginBottom: 24 }}>
            {currentQuestion.chips.map((chip) => (
              <button
                key={chip}
                className="chip"
                onClick={() => handleChipAnswer(currentQuestion.key, chip)}
                disabled={loading}
              >
                {chip}
              </button>
            ))}
          </div>

          <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 10 }}>
            Or type your answer:
          </p>
          <div style={{ display: 'flex', gap: 10 }}>
            <textarea
              value={freeText}
              onChange={(e) => setFreeText(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleFreeTextSubmit() } }}
              placeholder="Type here..."
              rows={2}
              disabled={loading}
              style={{ flex: 1 }}
            />
            <button
              className="btn-primary"
              onClick={handleFreeTextSubmit}
              disabled={!freeText.trim() || loading}
              style={{ alignSelf: 'flex-end', padding: '10px 16px' }}
            >
              {loading ? <LoadingDots /> : '→'}
            </button>
          </div>

          <div style={{ marginTop: 16, textAlign: 'right' }}>
            <button className="btn-ghost" onClick={handleSkip} disabled={loading}>
              Skip →
            </button>
          </div>
        </div>
      )}

      {error && (
        <p style={{ color: '#ef4444', marginTop: 16, fontSize: 14 }}>{error}</p>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Create frontend constants file**

```js
// frontend/src/constants.js
export const CATEGORY_CHIPS = ['Water Bottle', 'Smart Display', 'Kitchen Organizer']
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/Stage2.jsx frontend/src/constants.js
git commit -m "feat: Stage 2 guided question stepper with chips, free text, and skip"
```

---

### Task 11: ProductCard and Stage 3

**Files:**
- Create: `frontend/src/components/ProductCard.jsx`
- Create: `frontend/src/components/Stage3.jsx`

- [ ] **Step 1: Create ProductCard.jsx**

```jsx
// frontend/src/components/ProductCard.jsx
export default function ProductCard({ product, rank }) {
  const stars = product.rating ? `${'★'.repeat(Math.round(product.rating))}` : ''

  return (
    <div className="card" style={{ display: 'flex', gap: 16, padding: 20, marginBottom: 16 }}>
      {/* Image */}
      <a
        href={product.product_url}
        target="_blank"
        rel="noopener noreferrer"
        style={{ flexShrink: 0 }}
      >
        <img
          src={product.image_url}
          alt={product.title}
          style={{
            width: 80, height: 80, objectFit: 'contain',
            borderRadius: 8, background: '#f8f8fc',
          }}
          onError={(e) => { e.target.style.display = 'none' }}
        />
      </a>

      {/* Content */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 8 }}>
          <a
            href={product.product_url}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              fontSize: 15, fontWeight: 600, color: 'var(--text-primary)',
              textDecoration: 'none', lineHeight: 1.3,
            }}
          >
            {product.title}
          </a>
          <span style={{
            fontSize: 16, fontWeight: 700,
            background: 'var(--accent-gradient)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            backgroundClip: 'text', flexShrink: 0,
          }}>
            ${product.price?.toFixed(2)}
          </span>
        </div>

        {product.rating && (
          <div style={{ fontSize: 13, color: '#f59e0b', marginTop: 4 }}>
            {'★'.repeat(Math.round(product.rating))}
            {'☆'.repeat(5 - Math.round(product.rating))}
            <span style={{ color: 'var(--text-secondary)', marginLeft: 4 }}>
              {product.rating.toFixed(1)}
            </span>
          </div>
        )}

        <p style={{
          fontSize: 13, color: 'var(--text-secondary)',
          marginTop: 8, lineHeight: 1.5,
        }}>
          {product.explanation}
        </p>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create Stage3.jsx**

```jsx
// frontend/src/components/Stage3.jsx
import ProductCard from './ProductCard'
import SupplementBar from './SupplementBar'

export default function Stage3({ sessionId, products, supplementLog, onSupplement }) {
  return (
    <div>
      <h2 style={{ fontSize: 22, fontWeight: 700, marginBottom: 4 }}>
        Your matches
      </h2>
      <p style={{ color: 'var(--text-secondary)', marginBottom: 28, fontSize: 14 }}>
        {products.length} recommendations, ranked for you
      </p>

      <div id="results-top">
        {products.map((product, i) => (
          <ProductCard key={product.product_url + i} product={product} rank={i + 1} />
        ))}
      </div>

      <SupplementBar
        sessionId={sessionId}
        supplementLog={supplementLog}
        onSupplement={onSupplement}
      />
    </div>
  )
}
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ProductCard.jsx frontend/src/components/Stage3.jsx
git commit -m "feat: ProductCard and Stage 3 results grid"
```

---

### Task 12: SupplementBar

**Files:**
- Create: `frontend/src/components/SupplementBar.jsx`

- [ ] **Step 1: Create SupplementBar.jsx**

```jsx
// frontend/src/components/SupplementBar.jsx
import { useState } from 'react'
import { refineRecommendations } from '../api'

function LoadingDots() {
  return <span className="loading-dots"><span /><span /><span /></span>
}

export default function SupplementBar({ sessionId, supplementLog, onSupplement }) {
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async () => {
    if (!text.trim() || loading) return
    setLoading(true)
    setError(null)
    try {
      const data = await refineRecommendations(sessionId, text.trim())
      onSupplement(data.products, data.ai_response)
      setText('')
      // Scroll back to results
      document.getElementById('results-top')?.scrollIntoView({ behavior: 'smooth' })
    } catch (e) {
      setError('Something went wrong. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="supplement-bar">
      {/* AI response log (newest first) */}
      {supplementLog.length > 0 && (
        <div style={{ marginBottom: 10 }}>
          {supplementLog.slice(0, 3).map((entry, i) => (
            <div key={entry.timestamp} style={{
              fontSize: 13, color: 'var(--text-secondary)',
              padding: '6px 0',
              borderBottom: i < supplementLog.length - 1 ? '1px solid rgba(108,99,255,0.08)' : 'none',
            }}>
              <span style={{ color: 'var(--chip-text)', fontWeight: 600 }}>Assistant: </span>
              {entry.aiResponse}
            </div>
          ))}
        </div>
      )}

      {/* Input row */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <input
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit() }}
          placeholder='Refine: "under $20", "needs to be faster delivery", "actually for outdoor use"'
          disabled={loading}
          style={{
            flex: 1,
            border: '1.5px solid var(--chip-border)',
            borderRadius: 8,
            padding: '10px 14px',
            fontSize: 14,
            color: 'var(--text-primary)',
            background: '#fff',
            outline: 'none',
            fontFamily: 'inherit',
          }}
        />
        <button
          className="btn-primary"
          onClick={handleSubmit}
          disabled={!text.trim() || loading}
          style={{ padding: '10px 20px', whiteSpace: 'nowrap' }}
        >
          {loading ? <LoadingDots /> : 'Update →'}
        </button>
      </div>

      {error && (
        <p style={{ color: '#ef4444', marginTop: 8, fontSize: 13 }}>{error}</p>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/SupplementBar.jsx
git commit -m "feat: SupplementBar with refinement input, AI response log, and scroll-to-results"
```

---

### Task 13: End-to-end smoke test

- [ ] **Step 1: Start the backend**

```bash
cd /Users/sabrina/Projects/shopping-assistant-4/backend
source .venv/bin/activate
ANTHROPIC_API_KEY=<your-key> uvicorn main:app --reload --port 8000
```

Expected: `Application startup complete.`

- [ ] **Step 2: Start the frontend**

```bash
cd /Users/sabrina/Projects/shopping-assistant-4/frontend
npm run dev
```

Expected: `Local: http://localhost:5173`

- [ ] **Step 3: Test the water bottle flow**

Open `http://localhost:5173`. Type: `"I need a good gym water bottle, preferably insulated"`

Expected:
- Loading dots appear
- Stage 2 loads — `use_case` should be skipped (Claude inferred "gym"), first question should be `insulated` or `size_preference`
- Answer via chip
- After final question (or skipping), loading indicator appears
- Stage 3 loads with 5 product cards, each with title, price, rating, and a personal explanation

- [ ] **Step 4: Test the supplement bar**

In Stage 3, type `"actually I need it under $20"` in the supplement bar and press Enter or click Update.

Expected:
- Loading
- Products update
- AI response appears above the input (e.g., "Got it — filtering to under $20.")
- Page scrolls to the top of results

- [ ] **Step 5: Test unknown category flow**

Reload. Type `"I want something nice for my home"`.

Expected:
- Stage 2 shows the three category chips (Water Bottle / Smart Display / Kitchen Organizer)
- Clicking one advances to that category's question sequence

- [ ] **Step 6: Run full backend test suite one final time**

```bash
cd /Users/sabrina/Projects/shopping-assistant-4/backend
source .venv/bin/activate
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 7: Final commit**

```bash
cd /Users/sabrina/Projects/shopping-assistant-4
git add .
git commit -m "feat: complete AI shopping assistant — FastAPI backend + React frontend"
```

---

## Self-Review Notes

**Spec coverage check:**
- Stage 1 entry → Task 9 ✓
- Stage 2 guided questions, chips, skip, free text → Task 10 ✓
- Stage 3 product cards with explanations → Task 11 ✓
- Supplement bar, refinement loop, AI response log → Task 12 ✓
- Claude 4 call sites only → Task 4 ✓
- Session state → Task 3 ✓
- Question sequences per category → Task 2 ✓
- Visual style (indigo-violet gradient, glassmorphism nav) → Task 7 ✓
- Shopping bag hero icon → Task 9 ✓
- Error handling (unknown category chips, all questions skipped) → Task 5 + Task 10 ✓
- Recommendation engine unchanged → Task 5 ✓

**Type consistency:** `session_id` (snake_case) used consistently throughout. `next_question` shape `{key, text, chips}` defined in `main.py._next_question()` and consumed in `Stage2.jsx`. `ProductCard` shape `{title, price, rating, image_url, product_url, explanation}` defined in `main.py._format_product()` and consumed in `ProductCard.jsx`.

**Placeholder scan:** None found.
