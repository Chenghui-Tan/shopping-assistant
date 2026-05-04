# recommendation_Algorithem/explainability.py
"""
Grounded explanation generator.

Maps the rule_matches produced by the ranker into human-readable reasons.
This is the *only* place the human-readable rationale is constructed —
upstream the ranker emits opaque rule names; the frontend is read-only.
Keeping the mapping here means the explanation is by-construction grounded
in the same signals the ranker actually consumed.
"""
from typing import Iterable

# ---------------------------------------------------------------------------
# Rule → human-readable reason. Phrasing is generic enough to drop into a
# bulleted "why this fits" list. When a rule name is missing from this map
# the rule still contributed to the score but is not surfaced — preferable
# to inventing copy.
# ---------------------------------------------------------------------------
_RULE_TEXT: dict[str, str] = {
    # smart_display
    "voice_control":          "Hands-free voice control — useful when your hands are full or messy.",
    "kitchen_hub_or_recipe":  "Designed for kitchen and recipe use, not a generic tablet.",
    "family_scheduling":      "Family calendar / scheduling features built in.",
    "large_screen":           "Large screen — easier to follow recipes from across the counter.",
    "entertainment_features": "Streams video, supports cooking shows and recipe walkthroughs.",
    "smart_home_compatible":  "Voice-controllable for smart-home routines.",
    "smart_device_bundle":    "Bundled with a smart-home device — single-purchase setup.",
    "display_device":         "A real display device — not a sensor or speaker miscategorised.",

    # water_bottle
    "gym_suitable":         "Lightweight or athletic-grade build — fits a gym bag.",
    "insulated_gym":        "Double-wall insulation keeps drinks cold during a workout.",
    "daily_use":            "Designed for daily carry — ergonomic, leak-resistant.",
    "outdoor_capacity":     "Large capacity — fewer refills outdoors.",
    "insulated_outdoor":    "Holds temperature for hours — important on long trips.",
    "kids_design":          "Kid-friendly design and licensed character finish.",
    "kids_lightweight":     "Light enough for kids to carry without strain.",
    "insulated":            "Insulated — keeps drinks hot or cold as you asked.",
    "lightweight_size":     "Lightweight body — easy to throw in a bag.",
    "easy_clean":           "Dishwasher-safe / easy to clean — matches your stated preference.",

    # kitchen_organizer
    "cabinet_fit":            "Sized and shaped for cabinet shelves.",
    "cabinet_stackable":      "Stackable / expandable — claws back vertical cabinet space.",
    "countertop_suitable":    "Counter-friendly footprint — stays out of the way.",
    "countertop_aesthetic":   "Clean, modern look — won't visually clutter the counter.",
    "under_sink_fit":         "Bin / basket form factor — fits the awkward under-sink area.",
    "space_efficient":        "Built specifically to maximise tight spaces.",
    "visibility_easy_access": "Clear or compartmented — every item is visible at a glance.",
    "easy_install":           "Comes ready-assembled or as a modular set — minimal setup.",
}

# Rule patterns that take a parameter, e.g. structure_stackable, structure_drawer
_PREFIX_RULE_TEXT: dict[str, str] = {
    "structure_":            "Matches the organiser style you picked: ",
    "ecosystem_":            "Works with your existing voice ecosystem: ",
    "material_":             "Matches the bottle material you picked: ",
    "drinking_style_":       "Matches the drinking style you picked: ",
    "organiser_material_":   "Matches the organiser material you picked: ",
}

# Map of additional smart_display + organiser rules.
_RULE_TEXT.update({
    "wall_mountable":          "Wall-mountable — fits the placement you chose.",
    "kitchen_friendly_size":   "Compact enough to fit on a typical kitchen counter.",
    "compact_screen":          "Compact screen — small footprint as you asked for.",
    "mid_screen":              "Mid-size screen — readable while leaving counter space.",
    "large_screen_pref":       "Large screen — easy to read from across the room.",
    "no_camera_match":         "No camera — matches your privacy preference.",
    "visibility_clear":        "Clear / see-through build — every item visible at a glance.",
})


def reasons_from_rules(rule_matches: Iterable[str]) -> list[str]:
    """Convert raw rule_matches into a list of human-readable reasons."""
    out: list[str] = []
    for r in rule_matches or []:
        if r in _RULE_TEXT:
            out.append(_RULE_TEXT[r])
            continue
        for prefix, prefix_text in _PREFIX_RULE_TEXT.items():
            if r.startswith(prefix):
                tail = r[len(prefix):].replace("_", " ")
                out.append(prefix_text + tail + ".")
                break
    return out


def generate_explanation(product, preferences, rule_matches=None, features=None) -> str:
    """
    Build a 1–2 sentence explanation grounded in rule matches + rating.
    Returned as a single string for backward compatibility with callers
    that want one line; richer per-rule bullets come from
    `reasons_from_rules`.
    """
    rs = reasons_from_rules(rule_matches or [])
    rating = product.get("rating")
    parts: list[str] = []
    if rs:
        # Take up to two strongest reasons for the inline summary.
        parts.append(" ".join(rs[:2]))
    if rating and rating >= 4.5:
        parts.append(f"Customer rating: {rating:.1f}★.")
    if not parts:
        parts.append("Matches your stated budget and feature preferences.")
    return " ".join(parts)
