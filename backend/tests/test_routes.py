# backend/tests/test_routes.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "recommendation_Algorithem"))

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
def test_answer_unknown_session_returns_404(mock_engine, mock_claude):
    from main import app
    client = TestClient(app)

    resp = client.post("/session/answer", json={
        "session_id": "no-such-id",
        "question_key": "use_case",
        "answer": "Gym",
        "is_chip": True,
    })
    assert resp.status_code == 404


@patch("claude_client.client")
@patch("main.engine")
def test_recommend_returns_five_products(mock_engine, mock_claude):
    from main import app
    client = TestClient(app)

    # Start session with all questions already inferred
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

    mock_engine.recommend_with_relaxation.return_value = (_mock_products(5), "strict")
    mock_claude.messages.create.return_value = _mock_response(
        json.dumps(["Exp 1", "Exp 2", "Exp 3", "Exp 4", "Exp 5"])
    )

    resp = client.post("/session/recommend", json={"session_id": sid})
    assert resp.status_code == 200
    products = resp.json()["products"]
    assert len(products) == 5
    assert products[0]["explanation"] == "Exp 1"
    assert products[0]["title"] == "Product 0"


@patch("claude_client.client")
@patch("main.engine")
def test_refine_updates_preferences_and_returns_products(mock_engine, mock_claude):
    from main import app
    client = TestClient(app)

    # Start session
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

    mock_engine.recommend_with_relaxation.return_value = (_mock_products(5), "strict")
    mock_claude.messages.create.side_effect = [
        _mock_response(json.dumps({
            "preference_updates": {"price_max": 20},
            "ai_response": "Got it — filtering to under $20.",
        })),
        _mock_response(json.dumps(["Exp 1", "Exp 2", "Exp 3", "Exp 4", "Exp 5"])),
    ]

    resp = client.post("/session/refine", json={"session_id": sid, "text": "under $20"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["ai_response"] == "Got it — filtering to under $20."
    assert len(data["products"]) == 5

    updated = session_module.get_session(sid)
    assert updated["preferences"]["price_max"] == 20
    assert len(updated["supplement_log"]) == 1
