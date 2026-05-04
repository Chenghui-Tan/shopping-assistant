# backend/tests/test_questions.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from questions import get_question_queue, get_question, CHIP_TO_VALUE, CATEGORY_ALIASES


def test_all_unanswered_questions_returned():
    queue = get_question_queue("kitchen_organizer", {})
    # Order is preserved; first three are the original triad.
    assert queue[:3] == ["use_area", "pain_point", "structure_type"]


def test_answered_questions_skipped():
    prefs = {"use_area": "cabinet"}
    queue = get_question_queue("kitchen_organizer", prefs)
    assert "use_area" not in queue
    assert "pain_point" in queue


def test_all_answered_returns_empty():
    # Provide every key in the kitchen_organizer sequence so the queue empties.
    prefs = {
        "use_area": "cabinet",
        "pain_point": "not_enough_space",
        "structure_type": "stackable",
        "organizer_material": "plastic",
        "visibility_priority": "clear",
        "price_max": 20,
    }
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
