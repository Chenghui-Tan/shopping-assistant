# backend/claude_client.py
import json
import os
import anthropic

MODEL = "claude-opus-4-6"
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", "placeholder"))

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
You are a personal shopping assistant. Write a short (1-2 sentences) personal explanation
for why each product fits this specific customer. Use their actual words and context.
Be specific, not generic.
Return ONLY a JSON array of strings, exactly one string per product in the list.
Example: ["Perfect for gym sessions — insulated to keep drinks cold for hours.", ...]\
"""

_SUPPLEMENT_SYSTEM = """\
You are a personal shopping assistant. Extract any preference updates from the user's message
and write a short (1-2 sentences) conversational acknowledgement.
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
