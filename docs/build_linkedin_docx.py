"""
Build LinkedIn-ready Word document from the capstone architecture article.
Output: linkedin_article.docx (copy-paste directly into LinkedIn's article editor).
"""
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT = "/Users/sabrina/Projects/shopping-assistant-4/docs/linkedin_article.docx"

doc = Document()

# ── Default body style ────────────────────────────────────────────────────────
normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(11)

# ── Helpers ───────────────────────────────────────────────────────────────────
def h1(text):
    p = doc.add_heading(text, level=1)
    for r in p.runs:
        r.font.size = Pt(18)

def body(parts):
    """parts: list of (text, style_flags). style_flags in {'', 'b', 'i', 'bi'}."""
    p = doc.add_paragraph()
    for text, flags in parts:
        r = p.add_run(text)
        r.font.size = Pt(11)
        r.bold = "b" in flags
        r.italic = "i" in flags
    return p

def plain(text):
    body([(text, "")])

def bullet(parts, numbered=False):
    style = "List Number" if numbered else "List Bullet"
    p = doc.add_paragraph(style=style)
    for text, flags in parts:
        r = p.add_run(text)
        r.font.size = Pt(11)
        r.bold = "b" in flags
        r.italic = "i" in flags

def italic(text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(10)
    r.italic = True

# ── Title ─────────────────────────────────────────────────────────────────────
title = doc.add_heading(
    "I Built an AI Shopping Assistant. Then I Kept the AI Out of the Ranking.",
    level=0,
)
for r in title.runs:
    r.font.size = Pt(24)

# ── Intro ─────────────────────────────────────────────────────────────────────
plain('When people hear "AI shopping assistant," they assume the AI does '
      'everything — parses your request, picks products, ranks them, writes '
      'the explanation. One model, end-to-end.')

plain("For my capstone project at CSUEB, I built one that works the opposite way.")

plain("Claude handles language. Rule-based code handles the decision. The "
      "ranking — the step where the system chooses what to show the user — "
      "never touches the LLM.")

plain("This article is about why I drew that boundary, and how the architecture "
      "ended up looking.")

# ── Why I Built It ───────────────────────────────────────────────────────────
h1("Why I Built It")

plain("Existing AI shopping tools — Amazon Rufus, ChatGPT Shopping, "
      "Perplexity, Google Shopping — are good at finding products. They're "
      "not built to help you decide between them.")

plain("The difference matters. Once you have twenty smart displays in front "
      "of you, the bottleneck isn't finding more; it's choosing one. That's "
      "a different kind of problem — competing criteria (price, rating, "
      "delivery, features), shifting priorities across a conversation, "
      "trade-offs users don't realize they're making until after the "
      "purchase. Retrieval systems, even very smart ones, can't close that "
      "gap.")

body([("I wanted to build a system that models shopping as a ", ""),
      ("decision", "i"),
      (" problem, not a search query. That ambition is what forced every "
       "architectural choice below — including the one where I decided the AI "
       "shouldn't rank.", "")])

# ── Why This Approach Works ──────────────────────────────────────────────────
h1("Why This Approach Works")

plain("Before getting into specifics, here's what a split architecture — AI "
      "for language, rule-based code for ranking — buys you over a pure LLM "
      "wrapper:")

body([("Auditability. ", "b"),
      ('Every ranking has a visible weighted sum. When a reviewer asks "why '
       'is this #1?", I can point to numbers — no model interpretability '
       'tooling needed.', "")])

body([("Stability. ", "b"),
      ("When the Claude API version changes, the ranking doesn't. Only the "
       "language layer moves. The core decision logic stays reproducible "
       "across model updates — which is the baseline requirement for any "
       "system where the output has to be defensible.", "")])

body([("Cheap iteration. ", "b"),
      ("Ranking changes are Python edits. LLM changes are prompt edits. They "
       "never block each other, which meant I could tune the scoring function "
       "while simultaneously improving the parsing prompt, without coupling.", "")])

body([("Explainability by construction. ", "b"),
      ('Because every score component is preserved alongside the product, '
       'the "explain this ranking" step isn\'t a second AI inference — it\'s '
       'a lookup. The explanation cites the same numbers that produced the '
       'rank.', "")])

body([("The cost is obvious: I had to actually design the scoring function "
       "instead of letting a model infer one. But that cost was the whole "
       "point. The scoring function ", ""),
      ("is", "i"),
      (" the contribution.", "")])

# ── Section 1 ────────────────────────────────────────────────────────────────
h1("The Core Architectural Decision: A Trust Boundary")

plain("Most AI shopping tools have a transparency problem. You ask a question. "
      "A model returns a ranked list. You have no idea why those products, in "
      "that order.")

plain("For a decision-support system, that's disqualifying. If a user can't "
      "audit the ranking, they can't trust it. If the developer can't reproduce "
      "it, they can't debug it. If the ranking drifts as the model updates, "
      "the system is effectively non-deterministic in production.")

plain("So I drew a line:")

# Emphasized quote
body([("Claude does natural-language work. Deterministic code does ranking.", "bi")])

plain("Picture it as two stacked layers. On top, Claude does the language "
      "work: parsing preferences, asking clarifying questions, explaining "
      "trade-offs, generating lifecycle suggestions. Below it, a deterministic "
      "rule-based engine handles hard constraints, weighted scoring, and "
      "two-tier ranking. Claude's output flows into the engine; the engine's "
      "ranked output flows back through Claude for natural-language "
      "explanation. That handoff is the trust boundary.")

plain("The LLM is a translator — it turns messy human intent into structured "
      "preferences, and structured recommendations back into readable "
      "explanations. The ranking itself is pure code: given the same inputs, "
      "it always returns the same output, and every weight is visible.")

# ── Section 2 ────────────────────────────────────────────────────────────────
h1("The Runtime: Six Components, One Orchestrator")

plain("The system runs as four pieces at runtime plus two offline:")

body([("Runtime", "b")])
bullet([("React frontend", "b"),
        (" — a single-page app with four interaction stages: Onboarding, "
         "Elicitation Q&A, Recommendations, Refinement.", "")])
bullet([("FastAPI backend", "b"),
        (" — four endpoints (/start, /answer, /recommend, /refine) that "
         "orchestrate everything. All business logic lives here.", "")])
bullet([("Claude (Anthropic API)", "b"),
        (" — called at four specific sites (detailed below).", "")])
bullet([("Recommendation engine", "b"),
        (" — a Python module that filters, scores, and ranks. No AI "
         "dependencies.", "")])

body([("Offline", "b")])
bullet([("ETL pipeline", "b"),
        (" — Playwright scrapers that feed a normalized product catalog.", "")])
bullet([("Product DB", "b"),
        (" — a flat JSON file (products_clean.json) with 100 products across "
         "3 categories.", "")])

plain("The frontend never talks to Claude directly. Every LLM call goes through "
      "the backend, where it's wrapped, prompted, and parsed. This matters: it "
      "means the ranking logic and the LLM prompts evolve independently, and "
      "switching models is a one-file change.")

# ── Section 3 ────────────────────────────────────────────────────────────────
h1("Claude's Four Call Sites (None of Them Rank)")

plain("One of the most deliberate design choices was enumerating exactly where "
      "the LLM belongs — and where it doesn't.")

bullet([("Parse preferences", "b"),
        (' — convert a free-text message like "I need a smart display, budget '
         'is flexible, I cook a lot" into a structured profile (category, '
         'constraints, priorities).', "")],
       numbered=True)
bullet([("Generate clarifying questions", "b"),
        (" — when the profile is sparse, ask targeted follow-ups that narrow "
         "the decision space.", "")],
       numbered=True)
bullet([("Explain trade-offs per product", "b"),
        (" — for each recommendation, produce a one-sentence rationale "
         "grounded in the user's stated priorities.", "")],
       numbered=True)
bullet([("Lifecycle suggestions", "b"),
        (" — post-purchase ideas tailored to the chosen product (meal "
         "planning for a kitchen display, cleaning schedules for water "
         "bottles).", "")],
       numbered=True)

plain("Ranking is conspicuously absent from that list.")

plain("Every call site has a narrow, well-scoped prompt and a well-defined "
      "output schema. The backend validates Claude's response before it flows "
      "onward. If parsing fails, the system asks the user to rephrase — it "
      "doesn't improvise.")

# ── Section 4 ────────────────────────────────────────────────────────────────
h1("The Ranking Algorithm: Two-Tier Weighted Scoring")

plain("The recommendation engine is the heart of the system and the part I'm "
      "proudest of. It runs in four steps:")

body([("Step 1 — Hard Constraint Filter", "b")])
plain('Budget ceilings and delivery deadlines are non-negotiable. Products '
      'outside them are eliminated before scoring. No product ever gets '
      '"close enough" on a deal-breaker.')

body([("Step 2 — Build the Feasible Set", "b")])
plain("Typically reduces ~100 products to 10–20 candidates. Everything "
      "downstream operates only on this feasible set.")

body([("Step 3 — Two-Tier Weighted Scoring", "b")])
plain("Here's the part that matters architecturally. Each product gets scored "
      "at two levels:")

bullet([("General weights", "b"),
        (' — rating, price, delivery. These weights are dynamic: they\'re '
         'derived from the user\'s stated priorities, not hard-coded. A user '
         'who says "budget flexible, can wait for delivery" gets Rating 50% / '
         'Price 30% / Delivery 20%. A user on a tight deadline gets the '
         'weights shifted toward delivery.', "")])
bullet([("Feature weights", "b"),
        (" — category-specific attributes. For smart displays: voice control, "
         "screen size, smart-home integration, brand. For water bottles: "
         "insulation, capacity, durability. Each category has its own feature "
         "set and its own weight profile.", "")])

plain("The combined score is α × General + (1 − α) × Feature, where α is "
      "tuned per category based on how much the general attributes carry the "
      "decision.")

body([("Step 4 — Ranked Output", "b")])
plain("Sort descending. Top N returned. Every score component is preserved "
      "alongside the product so the explanation step can reach back into the "
      "ranking and cite the actual numbers.")

plain("The whole thing is deterministic. Re-run the same inputs, get the same "
      "output. Every weight is an integer the user can inspect.")

# ── Section 5 ────────────────────────────────────────────────────────────────
h1("The Data Layer: Less Glamorous, Most Of The Work")

plain("The ETL pipeline was by far the most practical engineering effort. A "
      "few things I learned:")

bullet([("Real delivery data is a string, not a date.", "b"),
        (' "Arrives Mar 14", "Get it in 2–3 days", "Ships within a week" — '
         'all different formats for the same concept. I wrote a normalizer '
         'that converts everything to an integer: days from today.', "")])
bullet([("Dedup needs two passes.", "b"),
        (" Exact URL matching catches the obvious duplicates; a fuzzy title "
         "prefix match (first 65 chars) catches the same product listed under "
         "two variants.", "")])
bullet([("Scrapers fail in creative ways.", "b"),
        (" I used a primary → fallback → supplement strategy per category: "
         "try Amazon first, fall back to Target if blocked, run supplemental "
         "queries until the target count is hit.", "")])

plain("The product schema is a single 10-field TypedDict — flat, boring, easy "
      "to reason about. I considered dimensional modeling early on. I don't "
      "regret choosing the flat version.")

# ── Closing takeaway ─────────────────────────────────────────────────────────
h1("The Bigger Takeaway")

plain("Most AI system design questions, in the end, boil down to one question: "
      "where do you put the trust boundary?")

plain('For a decision-support system, I don\'t think the answer is "wherever '
      'the LLM will go."')

plain("The interesting architectures are the ones that are deliberate about "
      "which parts of the system get the benefits of probabilistic intelligence "
      "and which parts stay deterministic. The LLM is incredible at parsing "
      "messy language. It's not the right tool for choosing what a person sees.")

plain("If you're designing AI-assisted systems where decisions need to be "
      "explainable, reproducible, and auditable — I'd love to compare notes.")

# ── Attribution + hashtags ────────────────────────────────────────────────────
italic("Built with React, TypeScript, FastAPI, Python, Claude (Anthropic), "
       "and Playwright. Applied Research Capstone, California State "
       "University, East Bay — April 2026.")

italic("#AI  #SoftwareArchitecture  #SystemDesign  #LLM  #AnthropicClaude  "
       "#DataEngineering  #DecisionSupport  #AppliedResearch  #Capstone")

# ── Save ──────────────────────────────────────────────────────────────────────
doc.save(OUT)
print(f"Saved → {OUT}")
