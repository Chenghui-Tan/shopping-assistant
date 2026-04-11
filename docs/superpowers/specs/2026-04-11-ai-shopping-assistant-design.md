# AI Shopping Assistant — Design Spec
**Date:** 2026-04-11
**Status:** Approved

---

## Overview

An AI-powered personal shopping assistant that guides customers from a vague need to a confident purchase decision in under 2 minutes. No forms, no browsing, no generic lists — just a short guided conversation and five curated recommendations with personal explanations.

---

## User Flow

### Stage 1 — Entry
Full-screen landing page. Hero section with a shopping bag icon (gradient indigo-violet badge, minimal line-art bag), title "AI Shopping Assistant", and subtitle "Tell me what you need, what matters to you, or what problem you're trying to solve." Single large text input, submit button.

On submit, the backend calls Claude to extract `{category, preferences_so_far}` from the raw text. If category cannot be determined, three category chips appear (Water Bottle / Smart Display / Kitchen Organizer) for the user to pick. Once category is known, advance to Stage 2.

### Stage 2 — Guided Questions
One question per screen. Progress bar (e.g. "Step 1 of 2") shows position in the question sequence for the detected category. Each screen shows:
- Question text
- Multiple-choice chips (category-specific options)
- Skip button
- "Or type your answer" free-text input below

Any question whose answer Claude already inferred from Stage 1 is silently removed from the queue. The user may see 0–3 questions depending on how much was already understood. After the last question (or if all are skipped), the app calls `/session/recommend` and advances to Stage 3.

### Stage 3 — Recommendations + Supplement
Five product cards appear. The supplement bar is permanently anchored at the bottom of the page from this point onward.

**Product card contents:**
- Product image (clicking opens the product URL in a new tab)
- Title, price, star rating
- Claude-written explanation — references the user's actual words and specific context, not generic tags

**Supplement bar behavior:**
- User types any refinement (e.g. "under $20", "I actually need it for outdoor use", "faster delivery")
- Claude extracts preference deltas and writes a short conversational response (e.g. "Got it — filtering to under $20 and prioritizing delivery speed")
- Preferences are merged with all existing preferences
- Recommendation engine re-runs with updated preferences
- Claude writes fresh explanations for the new top 5
- AI response appears in a supplement chat log (above the input, newest first)
- Page scrolls to updated recommendation cards
- Repeatable unlimited times

---

## UX Principles

1. **Always responsive** — Every action has immediate feedback. Buttons disable and show loading state. Dots animate while waiting. No silent hangs.
2. **Progressive reveal** — Stages appear only when needed. Nothing is shown before it's relevant. The page grows as the conversation deepens.
3. **Never repeat** — Questions only ask what isn't already known. If the user said "under $30" in Stage 1, the budget question never appears in Stage 2.
4. **Always a path forward** — No dead ends. Unknown category → category chips appear. No results → supplement bar is always there. Skip is always available.
5. **Input flexibility** — Every question offers chips for speed AND free text for nuance.
6. **Explanations feel personal** — Every "why this" reflects the user's actual words and context, not generic tags.
7. **Supplement is always there** — Once past Stage 1, the user can always add, correct, or refine. The system recalculates and scrolls them back to results.

---

## Visual Design

**Style:** Fresh & Modern (Option C)
- Background: soft indigo-violet gradient (`#f0f4ff` → `#faf0ff`)
- Nav: glassmorphism (`rgba(255,255,255,0.8)` + backdrop blur)
- Accent: indigo-violet gradient (`#6c63ff` → `#a855f7`)
- Progress bar: gradient fill on a pale indigo track
- Chips (selected): gradient fill + white text + subtle shadow
- Chips (unselected): white background + indigo border + indigo text
- Product cards: white, rounded corners, soft shadow
- Body text: `#1a1a2e` (headings), `#9ca3af` (secondary)

**Hero icon:** Shopping bag in a rounded-square gradient badge (56×56px, border-radius 16px, `box-shadow: 0 4px 16px rgba(108,99,255,0.35)`). Minimal line-art bag, white stroke on gradient background.

---

## Architecture

**Stack:** FastAPI (Python) backend + React frontend.

### API Endpoints

```
POST /session/start
  body:    { text: string }
  returns: { session_id, category, next_question | null, chips?: string[] }

POST /session/answer
  body:    { session_id, question_key, answer: string }
  returns: { next_question | null }
  # null = all questions done, frontend calls /session/recommend

POST /session/recommend
  body:    { session_id }
  returns: { products: ProductCard[] }

POST /session/refine
  body:    { session_id, text: string }
  returns: { products: ProductCard[], ai_response: string }
```

```typescript
// ProductCard shape
{
  title: string
  price: number
  rating: number
  image_url: string
  product_url: string
  explanation: string   // Claude-written, personal to this user
}
```

### Session State

Stored server-side in an in-memory dict keyed by `session_id` (UUID):

```python
{
  "session_id": "abc-123",
  "raw_input": "I need something for my messy kitchen cabinets",
  "category": "kitchen_organizer",
  "preferences": {
    "use_area": "cabinet",       # inferred from Stage 1
    "pain_point": None,          # unknown — will be asked
    "structure_type": None,      # unknown — will be asked
    "price_max": None,           # unknown — skipped (not in top 3)
    "priority": "balanced"       # default
  },
  "question_queue": ["pain_point", "structure_type"],
  "answered": ["use_area"],
  "recommendations": [],
  "supplement_log": []           # [{ user_text, ai_response, timestamp }]
}
```

### Question Sequences (max 3 per category)

| Category | Q1 | Q2 | Q3 |
|---|---|---|---|
| `kitchen_organizer` | use_area | pain_point | structure_type |
| `water_bottle` | use_case | insulated | size_preference |
| `smart_display` | use_case | price_max | delivery_days_max |

Any question already answered by Claude's parse of Stage 1 input is removed from the queue before Stage 2 begins.

**Chip options per question:**

| Question key | Chip labels |
|---|---|
| use_area | Cabinet · Countertop · Under the sink |
| pain_point | Not enough space · Hard to find things |
| structure_type | Stackable · Drawer · Bin · Expandable · Lazy Susan |
| use_case (water_bottle) | Gym · Daily carry · Outdoor · Kids |
| use_case (smart_display) | Cooking · Family · Entertainment · Smart home |
| insulated | Yes · No |
| size_preference | Lightweight · Large · No preference |
| price_max | Under $15 · Under $30 · Under $50 · No limit |
| delivery_days_max | ASAP (1–2 days) · This week · No preference |

---

## Claude Integration

Claude is called in exactly **4 places**:

### 1. `/session/start` — Parse initial input
**Purpose:** Extract `category` and any inferable preference values from raw user text.
**Output:** Structured JSON `{ category, preferences }`.
**When bypassed:** Never — always runs on Stage 1 submit.

### 2. `/session/answer` — Map free-text answer
**Purpose:** When a user types a free-text answer instead of selecting a chip, Claude maps the text to the structured preference value for that question key.
**When bypassed:** Chip selections bypass Claude entirely — value is set directly.

### 3. `/session/recommend` — Write card explanations
**Purpose:** After `recommend_products()` returns the top 5, Claude writes one personal explanation per card. Each explanation references the user's raw input, the question answers given, and the specific product features that match.
**Implementation:** One Claude call returning all 5 explanations as a JSON array. Single call keeps costs low and avoids rate limit risk.

### 4. `/session/refine` — Parse supplement input
**Purpose:** Extract preference deltas from the supplement bar text, merge with existing preferences, and write a short conversational acknowledgement (1–2 sentences).
**Output:** `{ updated_preferences, ai_response }`.

---

## Frontend Component Tree

```
App
├── Stage1
│   ├── HeroIcon (shopping bag badge)
│   ├── Title + Subtitle
│   └── TextInput + SubmitButton
├── Stage2
│   ├── ProgressBar
│   └── QuestionCard
│       ├── QuestionText
│       ├── ChipGroup
│       ├── SkipButton
│       ├── FreeTextInput
│       └── LoadingDots (while Claude parses free text)
└── Stage3
    ├── ResultsGrid
    │   └── ProductCard × 5
    │       ├── ProductImage (→ product_url)
    │       ├── Title, Price, Rating
    │       └── Explanation
    └── SupplementBar
        ├── SupplementLog (AI responses, newest first)
        ├── TextInput
        └── SubmitButton
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Category unclear after Stage 1 | Show three category chips — user picks one |
| Recommendation engine returns < 5 results | Show however many matched; no empty state |
| Claude call fails on free-text answer | Store raw text as preference value, continue |
| All 3 questions skipped | Proceed to recommendations with inferred preferences only |
| Supplement returns 0 results | Show AI response explaining the constraint; suggestions to relax it |

---

## Recommendation Engine Integration

The existing `recommend_products()` function in `recommendation_Algorithem/recommendation_engine_refactored.py` is used unchanged. The API layer translates session preferences into the dict format the engine expects and passes it directly. The engine handles filtering, scoring, ranking, and fallback logic.

Explanations generated by the existing `generate_explanation()` function are **replaced** by Claude-written explanations in this app. The Claude explanations are richer and reference the user's specific input.

---

## Out of Scope

- User accounts or saved sessions
- More than 3 product categories
- Persistent storage (in-memory sessions only)
- Mobile-specific layouts (desktop-first, responsive is a bonus)
- A/B testing or analytics
