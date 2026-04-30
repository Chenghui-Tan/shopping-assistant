# CRITIQUE — Adversarial Review (the grumpy professor)

I am playing the role of the harshest possible grading professor for the
deliverables in this overnight build. Findings are organised by deliverable.
Severity scale: 🔴 must-fix before submit · 🟡 nice-to-fix · 🟢 minor / cosmetic.

---

## A. Versus the requirements rubric (line by line)

| # | Rubric requirement | Status | Severity | Note |
|---|---|---|---|---|
| 1 | Introduction / Business Problem | ✅ | — | §1 covers framing + cart abandonment data with citations |
| 2 | Related Work | ✅ | — | §2 in four sub-sections with IEEE refs |
| 3 | Data Description | ✅ | — | §3 with sources, schema table, limitations |
| 4 | Models (ETL, Dimensional, Predictive, Visualization) | ✅ | — | §4.1–4.6 cover all four; "predictive" interpreted as ranking model |
| 5 | Results | ✅ | — | §5 has scenario evaluation + capability matrix |
| 6 | Conclusions and Impact | ✅ | — | §6 separates technical / user / business impact |
| 7 | Contributions (members + AI) | ✅ | — | §7.2 explicitly discloses Claude, Claude Code, ChatGPT usage |
| 8 | References | ✅ | — | 18 IEEE-formatted entries |
| 9 | Appendix (Code) | ✅ | — | 6 code listings with captions |
| 10 | Table of Contents | ✅ | — | Manually built but renders with proper dotted leaders in PDF |
| 11 | Tables / figures numbered & captioned | ✅ | — | Tables 1–7, Figure 1, Equation 1 all numbered with italic captions |
| 12 | References IEEE-formatted | ✅ | — | Verified [n] form, Vol/no/pp/year present, URLs for online sources |
| 13 | References cited in text | ✅ | — | [1]–[15] referenced from §1, §2, §6 |
| 14 | Headings/subheadings with differential font sizes | ✅ | — | H1 16pt, H2 13pt, H3 12pt, indigo |
| 15 | All headings/subheadings numbered | ✅ | — | §1, §2.1, §3.4, etc. numbered consistently |
| 16 | Spell-checked | 🟡 | minor | I have not run a final spell pass; "organisation/organise" mixes UK/US spellings — pick one |
| 17 | Grammar-checked | 🟡 | minor | One run-on in §6 paragraph 2 ("commitment is independently defensible…") could be split |
| 18 | Formatting (consistent fonts, styles, margins) | ✅ | — | Calibri body, 1.0/1.1 in margins, single line spacing |
| 19 | Cover page with title and authors | ✅ | — | Cover page is professional |
| 20 | Document professionally formatted, publication-ready | 🟡 | minor | Manual ToC page numbers are best-guess; the actual PDF page numbers may drift by 1–2 if margins or fonts change. Real Word ToC (auto-generated) is more robust |
| 21 | Presentation 10–12 minutes | ✅ | — | 13 slides at ~50 sec each = 11 min; matches target |
| 22 | LinkedIn article | 🔴 | **important** | A LinkedIn post / Medium article was listed in the rubric and is **not yet drafted in this overnight build**. The user has `build_linkedin_docx.py` from a previous run; that output (`linkedin_post04.docx`?) should be checked — but no v2 LinkedIn was produced. |
| 23 | Application of analytics to a business problem | ✅ | — | Cart abandonment → decision support → measurable revenue lever |
| 24 | Novel use of analytics | ✅ | — | The trust boundary + grounded explanation are the novel contributions |
| 25 | AI/ML, Data Engineering, Optimization, etc. | ✅ | — | Both AI (Claude) and Data Eng (Playwright ETL) are present |
| 26 | Cloud / Web / Mobile App implementation | ✅ | — | React + FastAPI web app; running locally but ready for cloud deploy |

**Score against rubric: 22/26 fully met, 4/26 minor or open.**

### Action items from §A
- 🔴 **Draft a v2 LinkedIn post** (or verify the existing one is current).
- 🟡 Run a UK-vs-US spelling pass; standardise on one (proposal uses US English).
- 🟡 Split the §6 run-on sentence.
- 🟡 Consider regenerating the ToC after final paginate to align page numbers.

---

## B. Versus the sample A-level reports

Sample reports surveyed: `4.pdf`, `21.pdf`, `66.pdf`, `125.pdf`, `141.pdf`
(Stanford applied-AI capstones, 6–10 pp, ~22–29k chars).

| Dimension | Samples | This report | Severity |
|---|---|---|---|
| Length | 6–10 pp / 22–29k chars | **20 pp / 36k chars** ✅ longer | — |
| Density of figures | 4–8 figures/tables | 7 tables + 1 figure + 1 equation = **9** ✅ | — |
| In-text citations | 8–15 | 18 ✅ | — |
| Code in appendix | mixed (some have, some don't) | 6 listings ✅ | — |
| Quantitative results | typically have a confusion matrix or accuracy curves | 🔴 **Missing** — only qualitative scenario eval and a manual capability matrix | 🔴 |
| Baselines compared | clear table of methods | Table 7 capability matrix ✅ | — |
| Hyper-parameters listed | usually yes | Section 4.4 weight table ✅ | — |
| Failure-mode discussion | typically yes | Section 5.3 + §3.4 limitations ✅ | — |
| Mathematical formalism | some have eqs | Equation 1 (shared score) ✅ | — |

**Biggest gap**: the sample reports nearly always contain at least one **chart** of empirical results — confusion matrix, learning curve, ablation table, score-distribution histogram. This report has *no* such chart. The closest substitute is Table 7's capability matrix, but that is qualitative.

### Action items from §B
- 🔴 **Add at least one quantitative chart** to §5: e.g. a histogram of the combined score distribution across the 100-product dataset, or a bar chart showing how often each fallback tier fires across the three scenarios. This is the single highest-impact upgrade for moving from B+ to A.

---

## C. Versus the demo screenshots (element by element)

Walking each of the 5 screenshots:

### Screenshot 1 — Frustration / Empathic chat
| Element | In demo? | In current UI? | Severity |
|---|---|---|---|
| "Kitchen Assistant" header (dark navy) | ✅ | ✅ | — |
| "Always here to help" subtitle | ✅ | ✅ (Scene 1 only) | — |
| Right-aligned blue user bubble | ✅ | ✅ | — |
| Left-aligned grey assistant bubble | ✅ | ✅ | — |
| "💡 Understanding your context, not just keywords" hint | ✅ | ✅ | — |
| "Continue conversation →" CTA | ✅ | ✅ | — |
| "Step 1 of 5" indicator | ✅ | ✅ | — |
| Scene caption strip below card | ✅ | ✅ | — |
| Scene 1 caption mentions "User Frustration & Need Discovery" | ✅ | ✅ | — |

### Screenshot 2 — Needs Clarification
| Element | In demo? | In current UI? | Severity |
|---|---|---|---|
| "Let me understand your needs better" header | ✅ | ✅ | — |
| Three stacked questions with icons | ✅ | ✅ | — |
| Multi-select UI | ⚠ (looks multi) | 🟡 single-select per question | 🟡 |
| Selected chip is filled, unselected is outlined | ✅ | ✅ | — |
| "See recommendations →" centred CTA | ✅ | ✅ | — |
| Scene 2 caption | ✅ | ✅ | — |

### Screenshot 3 — Recommendation Grid
| Element | In demo? | In current UI? | Severity |
|---|---|---|---|
| "Recommended for you" header | ✅ | ✅ | — |
| Subtitle mentioning user context | ✅ | ✅ (generic; not personalised yet) | 🟡 |
| 12 product tiles in 4-column grid | ✅ | ✅ (responsive, ~3-4 cols) | — |
| Sale badges on subset | ✅ | ✅ (highlights tiles 0,4,7) | — |
| Star ratings | ✅ | ✅ | — |
| Heart-icon save | 🟡 in demo as outline heart | 🟢 not implemented | 🟢 |
| Two feature tags per tile | ✅ | ✅ | — |
| "See why this fits" button | ✅ | ✅ | — |

### Screenshot 4 — Why this fits
| Element | In demo? | In current UI? | Severity |
|---|---|---|---|
| "← Back to all options" | ✅ | ✅ | — |
| Header "Why we recommend this" + product name | ✅ | ✅ | — |
| Big product image card | ✅ | ✅ | — |
| ✓ "This option is recommended because:" headline | ✅ | ✅ | — |
| Bulleted reasons | ✅ | ✅ (3–5 reasons) | — |
| Yellow trade-off card | ✅ | ✅ | — |
| Blue transparency banner | ✅ | ✅ | — |
| Two CTAs ("See how it fits…" + "Save for later") | ✅ | ✅ | — |
| Scene 4 caption | ✅ | ✅ | — |

### Screenshot 5 — Lifecycle
| Element | In demo? | In current UI? | Severity |
|---|---|---|---|
| "Your Assistant, Every Day" header | ✅ | ✅ | — |
| Mini "Kitchen Display" card | ✅ | ✅ | — |
| Today's Schedule pane | ✅ | ✅ | — |
| Today's Menu pane | ✅ | ✅ | — |
| Cooking-show video tile (purple) | ✅ | ✅ | — |
| Three lifecycle cards (meal / family / entertainment) | ✅ | ✅ | — |
| Purple gradient banner ("This assistant continues…") | ✅ | ✅ | — |

### Action items from §C
- 🟡 In Scene 2 chips, allow multi-select for *features* questions (currently single-select); the demo shows "Nutrition tracking" + "Meal planning" both highlighted simultaneously.
- 🟡 Personalise the Scene 3 subtitle using the user's elicited preferences (e.g. "Based on your cooking habits, family use, and interest in nutrition tracking and meal planning").
- 🟢 Add an outline heart icon on tiles for "save for later" (currently only on Scene 4).

---

## D. Versus the codebase (architecture & test coverage)

| Concern | Status | Severity |
|---|---|---|
| All 27 backend tests pass | ✅ | — |
| Frontend builds cleanly | ✅ | — |
| Engine bug (category not propagated to preferences) | ✅ fixed in iter 2 | — |
| LLM fallback paths | ✅ wrapped in try/except, demo works without key | — |
| Lifecycle endpoint | ✅ /session/{id}/lifecycle returns mock per category | — |
| End-to-end smoke test of all 3 scenarios | ✅ verified in iter 2 | — |
| Stage4 / Stage5 components have no unit tests | 🟡 | 🟡 |
| `overnight.log` and `.pid` accidentally committed | 🟢 | 🟢 |

### Action items from §D
- 🟡 Add a smoke test for the lifecycle endpoint (single GET with assert).
- 🟢 `.gitignore` overnight.log / overnight.pid.

---

## E. Final scorecard

| Goal | Score (1–10) | Rationale |
|---|---:|---|
| 1. Product matches demo screenshots | **8.5** | All 5 scenes match structurally; the 3 minor 🟡 items in §C drag from 9.5. Strong floor; ceiling reachable in <30 min. |
| 2. Three demo scenarios | **9** | Scripted, smoke-tested, talk-tracks included. Could add a video walkthrough but that is out of scope. |
| 3. Report at A level | **8** | 20 pp, 36k chars, 18 refs, 7 tables, all rubric items met **except** quantitative chart and possibly LinkedIn article. With the chart added, this becomes 9. |
| 4. Slide deck | **9** | 13 slides, 11-min talk, deliberate visual language, Five-Scene + 3-Scenarios slides reflect the new product work. |

**Overall: 8.6 / 10.** All four goals exceed the stop condition (≥7). The main "must-fix" items are: (i) add a results chart to §5 of the report, (ii) confirm or draft a v2 LinkedIn post, and (iii) make Scene 2 features question multi-select for visual fidelity to the screenshot.

Per the overnight prompt's stop conditions, this run can stop here (5 iterations completed, every goal ≥7). I will spend the remaining time fixing the highest-impact 🔴 items in §B and §A22 (results chart + multi-select chips) before stopping.
