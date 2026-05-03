"""
Decision-relevant attribute extraction for the shopping assistant.

The scraped dataset has only title / price / rating / delivery — the
decision questions (ecosystem, screen size, camera, mounting) need to be
inferred from the title text. This module centralises that inference so
both the ranker and the comparison view see the same values.

Each function returns either a structured value or None when the title
provides no signal — never a fabricated default.
"""
from __future__ import annotations

import re

# --- Screen size in inches ----------------------------------------------------

# Echo Show models embed the screen size in the model number.
# Echo Show 5 → 5.5", Show 8 → 8", Show 10 → 10.1", Show 11 → 11",
# Show 15 → 15.6", Show 21 → 21".
_ECHO_SHOW_SIZE = {
    5:  5.5, 8:  8.0, 10: 10.1, 11: 11.0, 15: 15.6, 21: 21.0,
}
_ECHO_RE = re.compile(r"\becho\s+show\s+(\d{1,2})\b", re.I)
# Generic "X-inch" / "X inch" / 'X"' anywhere in the title.
_INCH_RE = re.compile(r"(\d{1,2}(?:\.\d)?)[-\s]?(?:inch|\"|in\b)", re.I)


def screen_inches(title: str) -> float | None:
    if not title:
        return None
    m = _ECHO_RE.search(title)
    if m:
        return _ECHO_SHOW_SIZE.get(int(m.group(1)))
    m = _INCH_RE.search(title)
    if m:
        v = float(m.group(1))
        # Sanity: ignore numbers like 25-pc / 16oz that masqueraded.
        if 4 <= v <= 30:
            return v
    return None


# --- Voice ecosystem ----------------------------------------------------------

# A product can compatible with multiple ecosystems; we collect the
# union. Returned as a sorted list so equality checks are stable.
_ECOSYSTEM_PATTERNS = {
    "alexa":  [r"\balexa\b", r"\becho\b", r"\bfire\s*tv\b", r"\bring\b"],
    "google": [r"\bgoogle\s+assistant\b", r"\bnest\s+hub\b", r"\bgoogle\s+home\b"],
    "apple":  [r"\bhomepod\b", r"\bapple\s+home(?:kit)?\b", r"\bsiri\b"],
}


def ecosystems(title: str) -> list[str] | None:
    if not title:
        return None
    found = set()
    for eco, pats in _ECOSYSTEM_PATTERNS.items():
        for p in pats:
            if re.search(p, title, re.I):
                found.add(eco)
                break
    return sorted(found) if found else None


# --- Camera presence ----------------------------------------------------------

# Heuristic: Echo Show 8/10/15/21 + Nest Hub Max have cameras; Echo Show 5
# (newer revisions) and Nest Hub (gen2 without cam) do not. Picture frames
# generally don't. Bundled "Blink" or "video call" implies camera.
_HAS_CAMERA_HINT = re.compile(
    r"\b(blink|video\s+call|2\s*mp|5\s*mp|webcam|hd\s+camera)\b", re.I,
)
_NO_CAMERA_HINT = re.compile(
    r"\b(no\s+camera|camera-free|without\s+camera)\b", re.I,
)


def has_camera(title: str) -> bool | None:
    if not title:
        return None
    if _NO_CAMERA_HINT.search(title):
        return False
    if _HAS_CAMERA_HINT.search(title):
        return True
    # Echo Show + size heuristic
    m = _ECHO_RE.search(title)
    if m:
        size = int(m.group(1))
        # Show 5 had cameras; Show 5 (3rd gen) removed it. Without a
        # reliable cue we leave it None — the comparison view shows '?'.
        if size in (8, 10, 11, 15, 21):
            return True
        return None  # 5 is ambiguous
    if re.search(r"\bnest\s+hub\s+max\b", title, re.I):
        return True
    if re.search(r"\bdigital\s+(picture|photo)\s+frame\b", title, re.I):
        return False
    return None


# --- Mounting / placement ----------------------------------------------------

_MOUNTING_PATTERNS = {
    "wall":    [r"\bwall[-\s]?(mount|mountable|planner)\b"],
    "counter": [r"\bcountertop\b", r"\bdesk(?:top)?\b", r"\bstand\b"],
    "cabinet": [r"\bunder[-\s]?cabinet\b"],
    "tilt":    [r"\btilt\s+stand\b", r"\badjustable\s+stand\b"],
}


def mounting(title: str) -> list[str] | None:
    if not title:
        return None
    found = []
    for kind, pats in _MOUNTING_PATTERNS.items():
        for p in pats:
            if re.search(p, title, re.I):
                found.append(kind)
                break
    return sorted(set(found)) if found else None


# --- Bottle capacity (oz) ----------------------------------------------------

_OZ_RE = re.compile(r"\b(\d{2,3})\s*oz\b", re.I)


def capacity_oz(title: str) -> int | None:
    if not title:
        return None
    m = _OZ_RE.search(title)
    if m:
        v = int(m.group(1))
        if 8 <= v <= 128:
            return v
    return None


# --- Combined extraction ------------------------------------------------------

def extract_all(product: dict) -> dict:
    """Return a dict of every extractable attribute for this product.

    Used to enrich each product record once at load time so the engine
    and the comparison view share the same source of truth.
    """
    title = product.get("title") or ""
    cat = product.get("category", "")
    out: dict = {}
    if cat == "smart_display":
        out["screen_inches"] = screen_inches(title)
        out["ecosystems"]    = ecosystems(title)
        out["has_camera"]    = has_camera(title)
        out["mounting"]      = mounting(title)
    elif cat == "water_bottle":
        out["capacity_oz"]   = capacity_oz(title)
    return out
