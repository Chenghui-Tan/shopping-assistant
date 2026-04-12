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
