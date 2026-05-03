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


def add_supplement_log(
    session_id: str,
    user_text: str,
    ai_response: str,
    diff: dict | None = None,
) -> None:
    """Record a refine turn. `diff` captures preference deltas for continuity:
    {key: {"from": old_value, "to": new_value}}.
    """
    _sessions[session_id]["supplement_log"].append({
        "user_text":   user_text,
        "ai_response": ai_response,
        "diff":        diff or {},
        "timestamp":   datetime.now(timezone.utc).isoformat(),
    })


def diff_preferences(before: dict, after: dict) -> dict:
    """Return {key: {from, to}} for keys whose value changed.

    Skips keys absent from `after` (no overwrite) and keys whose value is
    semantically equal (None == None).
    """
    out: dict[str, dict] = {}
    for k, new_v in after.items():
        old_v = before.get(k)
        if old_v != new_v:
            out[k] = {"from": old_v, "to": new_v}
    return out
