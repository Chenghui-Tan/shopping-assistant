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
