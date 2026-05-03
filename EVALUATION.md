# EVALUATION — Self-Scoring vs. Rubric (v3)

Branch: `overnight-capstone-20260430` · Updated 2026-05-02 after a second iteration loop on the product (Iters A–E).

## Stop-condition check (overnight prompt)

| Condition | Status |
|---|---|
| 5 iterations completed | ✅ first loop = 6, second loop = 5 (A–E) |
| Every goal scores ≥ 7 | ✅ lowest = 9 |
| 8-hour budget | ✅ |
| `--max-turns` exhausted | ✅ not exhausted |

## Goal scores (1–10)

### Goal 1 — Product matches demo screenshots: **9.5 / 10**
- Five-scene flow. Tile bullets and feature tags now category-aware (no more "Hands-free voice control" on a $9 plastic bin).
- Sale badges removed (no real promotion data); save-for-later heart added on tiles + Stage 4 + counter pill at top.
- Multi-select on smart_display use_case actually OR-scores rules end-to-end.
- Scene 4 reasons are mapped from ranker rule_matches via a shared dictionary — the report's "grounded explanation" claim is now true in code.
- Scene 5 lifecycle has 10 distinct dashboards across 3 categories, branched on elicited preferences (a single user no longer sees "Soccer practice — Emma").
- Stage 1 reply is now contextual to the parsed use_case (8 distinct replies); Stage 2 chips pre-fill from LLM-inferred preferences when present.
- Constraint relaxation surfaces as an explicit yellow banner ("delivery filter dropped").
- Refine bar shows a per-turn "What changed" card with strikethrough old → blue new for each preference delta.
- Engine is defensively coerced against bad LLM output (Pydantic schema) and bad chip values (numeric coercion).
- Remaining: outline-heart on tiles is a unicode glyph rather than an SVG; some demos may want the SVG version. Cosmetic.

### Goal 2 — Three demo scenarios: **9.5 / 10**
- `docs/demo_scenarios.md` still ships scripted scenarios for kitchen / gym / cabinet.
- Each scenario now has a richer expected lifecycle dashboard (the soccer-practice schedule is genuinely earned only when "family" is picked).
- Iter B verified across **10** distinct preference combinations — well beyond the original three scenarios.
- Backfill in Iter A means delivery numbers shown in tiles are no longer fabricated for 72/100 products; they're flagged as "estimated" with a deterministic value.

### Goal 3 — Report at A level: **9.5 / 10**
- **21 pages, 41k chars** (was 20 pp, 36k in v2; samples are 6–10 pp / 22–29k).
- New §3.4 reflects the data backfill with provenance flags (scraped vs estimated vs synthesised).
- New §4.5 strengthens the explainability claim and references the shared rule→text dictionary.
- New §4.7 (preference continuity) and §4.8 (personalised lifecycle) — both new sections close the largest "claims-vs-code" gaps from the original CRITIQUE.md.
- §5.3 expanded from 3 to 5 behavioural observations covering relaxation visibility and continuity.
- ToC rebuilt with updated page numbers; all rubric items still met.
- Built deterministically by `docs/build_report_v5.py`; converted to PDF with LibreOffice headless.

### Goal 4 — Slide deck: **9 / 10**
- 13 slides (unchanged structure from v2). Output as `capstone_presentation_v3.pptx` and `.pdf`.
- Content still aligned with report; no fundamental layout changes were needed since the demo-flow and three-scenario slides were already added in v2.
- Improvement opportunity: a screenshot embedded into Slide 5 would be more vivid than the text-only layer cards.

## Aggregate

| | |
|---|---|
| Mean | **9.4 / 10** |
| Min | **9 / 10** |
| Stop-cond floor (≥ 7) | ✅ |
| 9-and-no-significant-findings | ✅ |

The four goals all clear the A-level bar with margin. The largest credibility-critical gaps from the original CRITIQUE.md are closed in code (not just commentary):

| Original CRITIQUE finding | Status now |
|---|---|
| Stage 4 reasons ungrounded in ranker rules | ✅ Iter 1 of patch loop + iter A of second loop. |
| Fake SALE badges and universal "Hands-free voice control" bullet | ✅ Iter 2 of patch loop. |
| Multi-select dropped all but first chip | ✅ Iter 3 of patch loop. |
| Constraint relaxation invisible | ✅ Iter 4 of patch loop. |
| LLM output trusted without validation | ✅ Iter 5 of patch loop (Pydantic). |
| 72/100 products had no delivery data | ✅ Iter A — provenance-flagged backfill. |
| Lifecycle identical for all users in a category | ✅ Iter B — 10 distinct dashboards. |
| `/refine` overwrote prefs with no continuity | ✅ Iter C — per-turn diff card. |
| Stage 1 reply was hardcoded 4-string lookup | ✅ Iter D — 8 use-case-aware replies. |
| Stage 2 asked questions Claude already answered | ✅ Iter D — chip pre-fill from inferred prefs. |
| "Save for later" was a no-op | ✅ Iter E.1 — toggle persistence + counter pill. |

What remains (all 🟢 or 🟡, none credibility-critical):
- LinkedIn v2 article still not drafted.
- Sessions are still in-process dict (refresh = lose state).
- Outline-heart icon is a unicode glyph, not an SVG.
- Slide 5 is text-only; a screenshot would be more vivid.

The product is in a state where every claim in the report can be demonstrated with a working button click. That's the bar I aimed for.
