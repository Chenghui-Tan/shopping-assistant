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
