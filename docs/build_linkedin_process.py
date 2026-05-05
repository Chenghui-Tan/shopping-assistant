"""
Build a fourth LinkedIn-ready Word document — behind-the-scenes / process
angle. Tools, agent, skills, tech, process, division of labor.

Output:
    docs/linkedin_article_process.docx
"""
from pathlib import Path
from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT = Path(__file__).parent / "linkedin_article_process.docx"


def make_doc():
    doc = Document()
    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    return doc


def h0(doc, text, size=24):
    p = doc.add_heading(text, level=0)
    for r in p.runs:
        r.font.size = Pt(size)


def h1(doc, text, size=16):
    p = doc.add_heading(text, level=1)
    for r in p.runs:
        r.font.size = Pt(size)


def body(doc, parts):
    """parts: list of (text, flags). flags ∈ {'', 'b', 'i', 'bi'}."""
    p = doc.add_paragraph()
    for text, flags in parts:
        r = p.add_run(text)
        r.font.size = Pt(11)
        r.bold = "b" in flags
        r.italic = "i" in flags


def plain(doc, text):
    body(doc, [(text, "")])


def bullet(doc, parts):
    p = doc.add_paragraph(style="List Bullet")
    for text, flags in parts:
        r = p.add_run(text)
        r.font.size = Pt(11)
        r.bold = "b" in flags
        r.italic = "i" in flags


def numbered(doc, parts):
    p = doc.add_paragraph(style="List Number")
    for text, flags in parts:
        r = p.add_run(text)
        r.font.size = Pt(11)
        r.bold = "b" in flags
        r.italic = "i" in flags


def italic(doc, text):
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.size = Pt(10)
    r.italic = True


# ════════════════════════════════════════════════════════════════════════════
doc = make_doc()

h0(doc, "Behind My MSBA Capstone: The Stack, the Workflow, and What an AI Pair-Programmer Actually Does")
italic(doc, "An honest breakdown of tools, process, and the human-AI division of labor")

plain(doc,
    "I just shipped my MSBA capstone — a five-scene conversational shopping assistant that turns "
    "vague frustrations into confident purchase decisions. The flow: Need Discovery → Clarification "
    "→ 3 Curated Picks → Why-this-fits → Lifecycle Support. Three product categories, a real ETL "
    "pipeline, a deterministic ranker, and LLM fallbacks at every language step.")
plain(doc,
    "This post is the behind-the-scenes breakdown: the stack, the agent I worked with, the "
    "iteration process, and how work was actually divided between me and the AI.")

# ── The stack ───────────────────────────────────────────────────────────────
h1(doc, "The stack")

body(doc, [("Frontend: ", "b"),
           ("React 18 + Vite 8, plain JavaScript, single-page app. The five-scene flow is "
            "component-per-scene; shared state lives in App.jsx and threads to children.", "")])
body(doc, [("Backend: ", "b"),
           ("Python 3.12 + FastAPI + Pydantic. Eight endpoints (/start, /answer, /recommend, "
            "/refine, /save, /saved, /lifecycle). 27 unit tests in pytest.", "")])
body(doc, [("Recommendation engine: ", "b"),
           ("Plain Python, no ML libraries. Filter → two-tier weighted score → rank → 3 curated "
            "picks (Best Fit / Budget / Stretch) → factual tradeoff labels. Lives in its own "
            "module so the trust-boundary is visible at the directory level.", "")])
body(doc, [("LLM layer: ", "b"),
           ("Claude Opus 4.7 via the official anthropic Python SDK. Three call sites: parse "
            "free text into structured preferences, map free-text answers, write personal copy + "
            "parse refine intent. Every call has a deterministic fallback (regex parser, category "
            "classifier, rule→text dictionary), so the demo runs without an API key.", "")])
body(doc, [("ETL: ", "b"),
           ("Playwright for Python, headless Chromium, anti-detection stealth (human-like delays, "
            "slow scroll). Scrapes Amazon and Target, normalizes via regex, deduplicates via URL "
            "exact + fuzzy title prefix. Output: 100 products in one JSON file with provenance "
            "flags (scraped vs. estimated vs. synthesised).", "")])
body(doc, [("Document pipeline: ", "b"),
           ("python-docx + python-pptx generate the .docx report and .pptx deck programmatically; "
            "LibreOffice headless converts to PDF; PyMuPDF reads PDFs back for verification.", "")])
body(doc, [("Tooling: ", "b"),
           ("Git on a long-running feature branch — about 50 commits, each one with the test "
            "pass/fail count in the body.", "")])

# ── The agent ──────────────────────────────────────────────────────────────
h1(doc, "The agent")
plain(doc,
    "I worked with Claude Code — Anthropic's official CLI agent — as my pair-programmer for "
    "roughly 80% of the implementation. It was not magic. Here is what made it useful:")

bullet(doc, [("Skills. ", "b"),
             ("Claude Code ships with named, scoped capabilities. I leaned on "
              "superpowers:writing-plans, superpowers:executing-plans, "
              "superpowers:test-driven-development, superpowers:systematic-debugging, "
              "superpowers:verification-before-completion, plus the document-specific skills "
              "document-skills:docx, document-skills:pptx, and document-skills:claude-api. "
              "Each skill is a small workflow with rules — TDD for example forces a "
              "'write the test, watch it fail, then write the code' cadence.", "")])
bullet(doc, [("Subagents. ", "b"),
             ("For broad codebase exploration I used the Explore subagent so the main thread "
              "stayed clean of file dumps.", "")])
bullet(doc, [("/loop slash command. ", "b"),
             ("I ran two overnight loops where the agent self-paced through "
              "'plan → execute → test → evaluate → improve' cycles. Each iteration was committed "
              "individually, so I could read the diff in the morning and either keep it or revert.", "")])
bullet(doc, [("Persistent memory + hooks. ", "b"),
             ("Auto-memory captured my preferences ('be terse, no trailing summaries') so I didn't "
              "have to repeat them every session. Hooks ran linters and tests on every commit.", "")])

# ── The process ────────────────────────────────────────────────────────────
h1(doc, "The process")
plain(doc, "I ran the project as an iteration loop, not a waterfall.")

numbered(doc, [("Brainstorm. ", "b"),
               ("Each major feature started with the brainstorming skill, which forces an explicit "
                "user-needs and trade-off discussion before any code is written.", "")])
numbered(doc, [("Plan. ", "b"),
               ("I wrote (or had Claude write) an implementation plan as a checklist with concrete "
                "file paths and line numbers. No 'AI-shaped' plans like 'improve the system' — every "
                "step was a single verifiable change.", "")])
numbered(doc, [("Execute. ", "b"),
               ("Pair-programmed the change with Claude Code as the typist and me as the reviewer. "
                "I declined more than I accepted in the early stages.", "")])
numbered(doc, [("Test. ", "b"),
               ("Backend tests in pytest; frontend builds with Vite; end-to-end HTTP smoke tests "
                "for every demo scenario after every iteration.", "")])
numbered(doc, [("Critique. ", "b"),
               ("Once a week I ran an adversarial review against the requirements rubric, the "
                "sample A-level reports, and the Figma demo screenshots. CRITIQUE.md became the "
                "queue for the next iteration.", "")])
numbered(doc, [("Commit. ", "b"),
               ("Every iteration ended with a single commit, message format <type>: <imperative>, "
                "body listing what changed and the test status.", "")])

plain(doc,
    "Two overnight loops near the end let Claude Code iterate self-paced (PROGRESS.md, "
    "CRITIQUE.md, EVALUATION.md, and HANDOFF.md as the artifacts of self-evaluation). When I "
    "woke up, I read the diff and the morning brief.")

# ── Division of labor ──────────────────────────────────────────────────────
h1(doc, "The division of labor")
plain(doc,
    "The single most important thing I want any future student to take from this: ")
body(doc, [("the AI is a competent typist and research assistant; you are the architect and the editor.", "bi")])

body(doc, [("What I owned:", "b")])
bullet(doc, [("Architecture. ", "b"),
             ("The five-layer decomposition, the trust boundary between language and ranking, the "
              "decision to ship deterministic fallbacks for every LLM call — all my calls.", "")])
bullet(doc, [("Critique. ", "b"),
             ("Every flaw the system has now is one I explicitly asked Claude to fix. The "
              "'Best Fit was 19oz when user picked Large capacity' bug, the 'lowest-cost lie' on "
              "the why-page, the speculative lifecycle copy ('the bottle is dumb, the schedule is "
              "yours') — those came out of human review.", "")])
bullet(doc, [("Voice. ", "b"),
             ("The product copy, the report tone, these LinkedIn articles. AI drafts; I edit.", "")])

body(doc, [("What Claude owned:", "b")])
bullet(doc, [("Implementation throughput. ", "b"),
             ("Boilerplate React components, FastAPI endpoint scaffolds, regex parsers, test cases.", "")])
bullet(doc, [("Refactoring speed. ", "b"),
             ("'Move this logic from main.py into the engine module and add a fallback' is "
              "something I would spend a day on alone; Claude does it in five minutes.", "")])
bullet(doc, [("Cross-file consistency. ", "b"),
             ("When I added a new attribute, Claude updated the extractor, the ranker, the format "
              "function, the frontend type, and the test fixtures in one pass.", "")])

plain(doc,
    "Net: this capstone took me 12 weeks. Without Claude Code as a pair-programmer it would have "
    "taken twice that. With Claude Code unsupervised, it would have looked impressive in a demo "
    "and fallen apart on inspection. The product is good because the loop was tight: AI proposes, "
    "human disposes, tests verify.")

# ── What I'd tell another student ──────────────────────────────────────────
h1(doc, "What I'd tell another student")
numbered(doc, [("Set the architectural commitments first. ", ""),
               ("(For me: trust boundary, five layers, deterministic ranker.)", "i")])
numbered(doc, [("Build the deterministic fallback ", ""), ("before", "i"), (" the LLM call.", "")])
numbered(doc, [("Write the rubric self-evaluation as a living file you update each iteration — "
                "not as a final-week panic.", "")])
numbered(doc, [("Treat the AI as a junior engineer with an excellent memory and zero judgment.", "")])
numbered(doc, [("Read every diff. Don't auto-merge.", "")])

plain(doc,
    "Happy to go deeper into any of the layers if useful. Drop me a line if you'd like a "
    "walkthrough of the repo or the iteration logs.")

doc.save(OUT)
print(f"saved {OUT}")
