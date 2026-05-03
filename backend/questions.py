# backend/questions.py
from typing import Any


class Question(dict):
    pass  # TypedDict-style: {key: str, text: str, chips: list[str]}


QUESTION_SEQUENCES: dict[str, list[dict]] = {
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
        # Multi-select on use_case captures what the screen has to be good at.
        {
            "key": "use_case",
            "text": "What's the main thing you'll use it for?",
            "chips": ["Cooking", "Family calendar", "Entertainment", "Smart home control"],
        },
        # Ecosystem question is one of the strongest filters: an Apple
        # household isn't going to be happy with an Echo, full stop.
        {
            "key": "voice_ecosystem",
            "text": "Do you already use a voice ecosystem?",
            "chips": ["Alexa", "Google", "Apple", "I'm new to this"],
        },
        # Where it lives drives mounting and screen-size sanity.
        {
            "key": "placement",
            "text": "Where will it live?",
            "chips": ["Kitchen counter", "Wall mount", "Living room", "Bedroom"],
        },
        # Decisive for cooking specifically — readability vs counter footprint.
        {
            "key": "screen_size_priority",
            "text": "How big does the screen need to be?",
            "chips": ["Compact (under 8\")", "Mid (8–11\")", "Large (15\"+)",
                      "Doesn't matter"],
        },
        # Privacy is the single most-asked follow-up about Echo Shows.
        {
            "key": "privacy_camera",
            "text": "Any privacy preference about the camera?",
            "chips": ["Camera is fine", "Prefer no camera", "Doesn't matter"],
        },
        {
            "key": "price_max",
            "text": "What's your budget?",
            "chips": ["Under $100", "Under $150", "Under $250", "No limit"],
        },
    ],
}

CATEGORY_CHIPS = ["Water Bottle", "Smart Display", "Kitchen Organizer"]

CATEGORY_ALIASES: dict[str, str] = {
    "Water Bottle": "water_bottle",
    "Smart Display": "smart_display",
    "Kitchen Organizer": "kitchen_organizer",
}

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
        "Under $250": 250,
        "No limit": None,
    },
    "voice_ecosystem": {
        "Alexa":             "alexa",
        "Google":            "google",
        "Apple":             "apple",
        "I'm new to this":   "none",
    },
    "placement": {
        "Kitchen counter":   "kitchen",
        "Wall mount":        "wall",
        "Living room":       "living_room",
        "Bedroom":           "bedroom",
    },
    "screen_size_priority": {
        "Compact (under 8\")": "compact",
        "Mid (8–11\")":         "mid",
        "Large (15\"+)":        "large",
        "Doesn't matter":       "any",
    },
    "privacy_camera": {
        "Camera is fine":     "ok",
        "Prefer no camera":   "no_camera",
        "Doesn't matter":     "any",
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


def get_question(category: str, key: str) -> dict | None:
    """Return the question definition for a given category and key."""
    questions = QUESTION_SEQUENCES.get(category, [])
    return next((q for q in questions if q["key"] == key), None)
