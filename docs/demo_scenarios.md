# Demo Scenarios — Live Walkthroughs

Three scripted scenarios for the capstone live demo, one per product category.
Each scenario runs end-to-end through the same five-scene flow:

> Frustration → Clarification → Recommendations → Why-this-fits → Lifecycle

The mock data is already seeded in `data/clean/products_clean.json`
(35 kitchen organizers, 35 water bottles, 30 smart displays). No setup is
required beyond starting the backend (`uvicorn main:app --reload --port 8000`)
and frontend (`npm run dev` in `frontend/`).

If `ANTHROPIC_API_KEY` is not set, the backend gracefully falls back to
chip-only navigation and the deterministic explanation engine — every scenario
below works in that mode.

---

## Scenario 1 — Kitchen Assistant for a busy parent (Smart Display)

**User profile:** *Sarah, 38, working parent of two. Cooks dinner most nights, struggles to follow recipes on her phone screen while her hands are messy.*

### Scene 1 — Frustration
**Type into the chat:**

> *"I cook almost every day, but I usually search recipes on my phone. The screen is too small, and it's really inconvenient to check while cooking."*

**Expected:** the assistant replies with an empathic acknowledgement
("That sounds frustrating. Would you like a larger screen that can guide you
hands-free…") and a `Continue conversation →` button.

### Scene 2 — Clarification
**Pick chips:**

| Question | Pick |
|---|---|
| *What's the main thing you'll use it for?* | **Cooking** |
| *What's your budget?* | **Under $150** |
| *How soon do you need it?* | **No rush** |

Click **See recommendations →**.

### Scene 3 — Recommendations
**Expected top tile:** an Echo Show 5 / Echo Show 8 model (~$50–$150) ranked
above non-display devices like sensors or speakers — the engine's
`is_display_device` rule gates non-displays out of category scoring.

### Scene 4 — Why this fits
Click **See why this fits** on the top tile. Expected reasons include:
- 15.6" / 8" screen makes recipes easy to follow while cooking
- Hands-free voice control via Alexa
- Built-in meal planning + nutrition support
- Trade-off: larger model takes more counter space

### Scene 5 — Lifecycle
Click **See how it fits your daily life →**. Lifecycle dashboard shows:
- **Today's Schedule:** soccer practice 9:00 AM, grocery delivery 2:00 PM, family dinner 6:00 PM
- **Today's Menu:** Greek yogurt & granola, chicken salad wrap, teriyaki salmon bowl
- **Cooking show video:** "Quick weeknight meals"
- **Cards:** Meal Planning · Family Hub · Entertainment

**Talk-track:** *"This is the moment that separates the assistant from a typical product page — the purchase doesn't end the relationship, it starts a daily routine."*

---

## Scenario 2 — Gym hydration for a runner (Water Bottle)

**User profile:** *Mike, 27, runs 3× per week, hates sweating with a heavy bottle, loses track of how much water he's drinking.*

### Scene 1 — Frustration
**Type:**

> *"I keep losing track of how much water I drink during workouts. My current bottle is heavy and leaks in my gym bag."*

**Expected:** assistant suggests a "lightweight, leak-proof bottle that keeps drinks cold and is easy to track on the go."

### Scene 2 — Clarification
| Question | Pick |
|---|---|
| *What will you mainly use it for?* | **Gym** |
| *Hot or cold drinks?* | **Yes, insulated** |
| *Any size preference?* | **Lightweight** |

### Scene 3 — Recommendations
**Expected top tile:** an Owala FreeSip 19–24oz stainless steel insulated bottle
in the $14–$30 range. The engine boosts insulated + lightweight + Owala/FreeSip
keywords for the `gym` use case and soft-penalises bottles missing them.

### Scene 4 — Why this fits
Reasons:
- Double-wall insulation keeps drinks cold for hours mid-workout
- Lightweight at 16–19 oz — easy to clip to a gym bag
- High customer rating (4.8★)
- Trade-off: insulation adds slight weight vs. plain plastic; worth it for cold drinks

### Scene 5 — Lifecycle
Lifecycle dashboard tailored to hydration:
- **Today's Schedule:** morning workout 7:00 AM, refill at lunch, evening run
- **Goal:** 100 oz/day, sip every 20 min
- **Video:** "Hydrate before, during, after"
- **Cards:** Hydration Tracker · Workout Companion · Flavor Ideas

**Talk-track:** *"The post-purchase value here is behavioural — the assistant nudges him toward his hydration goal and suggests flavor variations so the bottle keeps earning its place in his routine."*

---

## Scenario 3 — Cabinet chaos rescue (Kitchen Organizer)

**User profile:** *Priya, 31, just moved into a smaller apartment. Cabinets are crammed; she wastes time hunting for things every morning.*

### Scene 1 — Frustration
**Type:**

> *"My kitchen drawers are a mess — I waste time every morning hunting for the right utensil and the cabinets feel chaotic."*

**Expected:** assistant says *"Mornings should be calm, not stressful…"* and
proposes organizers that make every utensil easy to grab.

### Scene 2 — Clarification
| Question | Pick |
|---|---|
| *Where's the problem area?* | **Cabinets** |
| *Biggest frustration?* | **Not enough space** |
| *Type of organizer?* | **Stackable** |

### Scene 3 — Recommendations
**Expected top tiles:** Brightroom stackable bins, drawer flatware organizers,
clear pantry bins in the $7–$25 range, all ≥ 4.8★. Lazy susans appear
when `pain_point=hard_to_find_things` is picked instead.

### Scene 4 — Why this fits
Reasons:
- Stackable / expandable design maximises vertical space
- Clear bins make contents visible at a glance
- 4.9★ rating signals dependable quality
- Trade-off: stackable bins require a small initial setup but pay back daily

### Scene 5 — Lifecycle
Lifecycle dashboard tailored to organization:
- **Today's Schedule:** Mon pantry restock, Wed wipe lazy susan, Sat grocery run
- **Status:** Cabinet bins clear / Drawer sorted / Counter visible
- **Video:** "Kitchen reset: 10-minute weekly tidy"
- **Cards:** Stay Organized · Smart Restock · Calm Counters

**Talk-track:** *"Organization is a habit, not a one-time purchase. The lifecycle layer turns the assistant into a weekly nudge that keeps the system from slipping back into chaos."*

---

## Demo run-of-show (recommended order, ~6–7 minutes total)

1. **Scenario 1 (Kitchen Assistant)** — your headline scenario; lingers on Scene 4 + 5 to highlight explainability + lifecycle. ~3 min.
2. **Scenario 2 (Water Bottle)** — fast walkthrough; emphasises preference elicitation working for a different domain. ~2 min.
3. **Scenario 3 (Kitchen Organizer)** — fastest; emphasises that the same five-layer architecture generalises across product categories. ~1 min.

After Scenario 1, refine with the supplement bar:
- Type **"actually under $80"** — top tiles re-rank toward Echo Show 5 / Dot models and ai_response acknowledges the change.

## Operational notes for the operator

- **Backend port:** 8000. **Frontend port:** 5173 (Vite default).
- **API key:** `ANTHROPIC_API_KEY` env var. With a real key, Scene 1 and Scene 3 use Claude for parsing/explanations. Without one, the system falls back to deterministic chip-only paths and engine-generated explanations — everything still works.
- **Reset between scenarios:** click any earlier dot in the step indicator to jump back; or refresh the page (sessions are in-memory).
- **Pre-seeded products:** all three categories already have ≥ 30 items in `data/clean/products_clean.json`; no scrape or DB load is needed for the demo.
- **Failure modes to be aware of:** if a tile shows no image, the placeholder icon renders (image URLs from Target/Amazon occasionally rotate). The recommendation rank is unaffected.
