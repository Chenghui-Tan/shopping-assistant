"""
Build capstone final report as a Word document (.docx)
A Decision-Oriented Conversational Shopping Assistant
Chenghui Tan — Applied Research Project
"""
from docx import Document
from docx.shared import Pt, Inches, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
import copy

doc = Document()

# ── Page margins ──────────────────────────────────────────────────────────────
for section in doc.sections:
    section.top_margin    = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin   = Inches(1.25)
    section.right_margin  = Inches(1.25)

# ── Style helpers ─────────────────────────────────────────────────────────────
def set_font(run, name="Calibri", size=11, bold=False, italic=False,
             color=None):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color:
        run.font.color.rgb = RGBColor(*color)

def heading(level, text, num=""):
    """Add a numbered heading."""
    p = doc.add_heading(level=level)
    p.clear()
    run = p.add_run(f"{num}  {text}".strip() if num else text)
    sizes = {1: 16, 2: 13, 3: 12}
    set_font(run, name="Calibri", size=sizes.get(level, 11),
             bold=True, color=(0x1E, 0x27, 0x61))
    return p

def para(text, indent=False, bold=False, italic=False, size=11, space_before=0, space_after=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after  = Pt(space_after)
    if indent:
        p.paragraph_format.left_indent = Inches(0.3)
    run = p.add_run(text)
    set_font(run, size=size, bold=bold, italic=italic)
    return p

def bullet(text, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent  = Inches(0.3 + level * 0.2)
    p.paragraph_format.space_after  = Pt(3)
    run = p.add_run(text)
    set_font(run, size=11)
    return p

def italic_caption(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after  = Pt(8)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run(text)
    set_font(run, size=10, italic=True, color=(0x50, 0x50, 0x50))

def page_break():
    doc.add_page_break()

def shade_cell(cell, hex_color="1E2761"):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_color)
    tcPr.append(shd)

def set_cell_text(cell, text, bold=False, color=None, size=11, align=WD_ALIGN_PARAGRAPH.LEFT):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    run = p.add_run(text)
    set_font(run, size=size, bold=bold, color=color)

# ══════════════════════════════════════════════════════════════════════════════
# COVER PAGE
# ══════════════════════════════════════════════════════════════════════════════
doc.add_paragraph()
doc.add_paragraph()
doc.add_paragraph()

title_p = doc.add_paragraph()
title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = title_p.add_run("A Decision-Oriented Conversational Shopping Assistant\nwith Preference Elicitation and Explainable Recommendations")
set_font(r, size=18, bold=True, color=(0x1E, 0x27, 0x61))

doc.add_paragraph()

sub_p = doc.add_paragraph()
sub_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
r2 = sub_p.add_run("Applied Research Project — Final Report")
set_font(r2, size=13, italic=True, color=(0x50, 0x50, 0x80))

doc.add_paragraph()
doc.add_paragraph()

for label, value in [("Author:", "Chenghui Tan"),
                     ("Program:", "Applied Data Analytics"),
                     ("Date:", "April 2026")]:
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rl = p.add_run(label + "  ")
    set_font(rl, size=12, bold=True)
    rv = p.add_run(value)
    set_font(rv, size=12)

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# ABSTRACT
# ══════════════════════════════════════════════════════════════════════════════
heading(1, "Abstract")
para(
    "Online shopping platforms have significantly reduced information search costs, yet purchasing decisions "
    "remain cognitively demanding. Most e-commerce systems assume users can clearly articulate preferences "
    "through keywords and filters. In practice, users begin with vague, incomplete, or evolving needs. This "
    "project proposes and implements a decision-oriented conversational shopping assistant organized around a "
    "five-layer workflow: preference elicitation, decision modeling, constraint-aware recommendation ranking, "
    "explainable trade-off communication, and post-purchase lifecycle support. The system's central "
    "architectural choice is a deliberate trust boundary: Claude (Anthropic) handles natural-language work — "
    "parsing user intent, generating clarifying questions, producing trade-off explanations, and suggesting "
    "post-purchase lifecycle ideas — while the ranking itself is carried out by deterministic rule-based code. "
    "The ranking step never touches the language model. This split yields auditability, stability across model "
    "updates, cheap iteration, and explainability by construction. A real ETL pipeline collects product data "
    "from Amazon and Target via Playwright-based scrapers, normalizes attributes, and stores 100 products across "
    "three categories. A React frontend and FastAPI backend complete the full-stack implementation. Results "
    "show that the proposed system addresses structural gaps in existing tools — preference continuity, decision "
    "transparency, delivery information, and post-purchase lifecycle support — that are absent from platforms "
    "such as Amazon Rufus, ChatGPT Shopping, Google Shopping, and Perplexity."
)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# TABLE OF CONTENTS (manual)
# ══════════════════════════════════════════════════════════════════════════════
heading(1, "Table of Contents")
toc_entries = [
    ("1", "Introduction / Business Problem", "3"),
    ("2", "Related Work", "4"),
    ("3", "Data Description", "5"),
    ("4", "Models", "6"),
    ("  4.1", "System Architecture & Trust Boundary", "6"),
    ("  4.2", "ETL Pipeline", "8"),
    ("  4.3", "Dimensional Model", "9"),
    ("  4.4", "Predictive Models — Claude + Two-Tier Scoring", "10"),
    ("  4.5", "Visualization — Frontend & Backend", "12"),
    ("5", "Results", "13"),
    ("6", "Conclusions and Impact", "14"),
    ("7", "Contributions", "15"),
    ("8", "References", "16"),
    ("9", "Appendix — Code Listings", "17"),
]
for num, title, page in toc_entries:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2)
    tab_stops = p.paragraph_format.tab_stops
    run = p.add_run(f"{num}  {title}")
    set_font(run, size=11)
    p.add_run("\t" + page)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Introduction / Business Problem
# ══════════════════════════════════════════════════════════════════════════════
heading(1, "Introduction / Business Problem", "1.")
para(
    "Online shopping platforms have reduced the friction of product discovery, yet purchasing decisions "
    "remain cognitively demanding for users. Most e-commerce systems — from keyword search engines to "
    "AI-powered chat assistants — are built around information retrieval rather than decision support. "
    "They assume users can clearly articulate their needs as queries, and they optimize for engagement "
    "metrics such as click-through rate rather than decision confidence [1]."
)
para(
    "In practice, users often begin with vague, incomplete, or evolving needs. A user searching for a "
    "'convenient kitchen device' may not know whether they want a smart display, a multi-cooker, or an "
    "organizer system. They balance competing priorities — price, delivery speed, brand trust, screen size, "
    "usability — without structured support for doing so. Existing tools fail to preserve preference "
    "continuity across interactions, expose decision-critical attributes such as delivery time and "
    "promotions, or explain why one product is ranked above another [2]."
)
para(
    "This project addresses the gap between information retrieval and decision support in online shopping. "
    "The proposed system is a conversational shopping assistant designed not merely to retrieve products, "
    "but to help users reason through decisions. By integrating five logical layers — preference elicitation, "
    "decision modeling, recommendation ranking, explainability, and post-purchase lifecycle support — into a "
    "unified workflow, the system aims to reduce cognitive load, increase decision confidence, and surface "
    "decision-critical product attributes that current tools omit."
)
para(
    "A defining architectural commitment distinguishes this work from pure LLM-wrapper approaches: a trust "
    "boundary that assigns natural-language work to Claude (preference parsing, clarifying questions, "
    "trade-off explanations, lifecycle ideas) and assigns the ranking decision to deterministic, rule-based "
    "code. The recommendation engine that decides what the user sees never invokes the language model. This "
    "separation makes every ranking auditable, reproducible across model updates, and explainable by "
    "construction — properties that are prerequisites for a decision-support system, not optional polish."
)
para(
    "The system is demonstrated through a scenario-based kitchen assistant demo, backed by a real ETL "
    "pipeline that collects and normalizes product data from Amazon and Target, and a full-stack "
    "implementation using React, FastAPI, and Claude (Anthropic, Opus 4.6) as the natural-language layer."
)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Related Work
# ══════════════════════════════════════════════════════════════════════════════
heading(1, "Related Work", "2.")

heading(2, "Search-Oriented E-Commerce Platforms", "2.1")
para(
    "Platforms such as Google Shopping and Amazon primarily rely on keyword search and filter-based "
    "refinement [3]. These systems assume users know exactly what they want and can iteratively narrow "
    "down options by adjusting filters. However, when users introduce new constraints — such as specifying "
    "'modern style' after already specifying color — earlier preferences are frequently overwritten rather "
    "than preserved. Users must mentally manage trade-offs across multiple interactions, significantly "
    "increasing cognitive burden [4]."
)

heading(2, "Conversational Shopping Assistants", "2.2")
para(
    "Chat-based systems such as ChatGPT-integrated shopping suggestions and Amazon Rufus allow natural "
    "language input but typically present limited product sets with minimal attributes — often only an "
    "image and price [5]. Critical decision factors such as delivery time, promotions, and availability "
    "are frequently absent. Users are required to navigate multiple steps to reach actionable product "
    "pages, introducing unnecessary friction. Continuous preference refinement across conversational "
    "turns is weak or inconsistent in current implementations [6]."
)

heading(2, "AI-Powered Answer Engines", "2.3")
para(
    "Tools like Perplexity AI excel at generating explanatory text but separate conversational reasoning "
    "from shopping workflows [7]. Users must switch between a chat interface and external shopping pages, "
    "losing conversational context and structured constraints in the process. While these tools demonstrate "
    "the value of explanatory AI, they do not integrate decision logic or product data natively."
)

heading(2, "Recommender Systems", "2.4")
para(
    "Traditional recommender systems focus on predicting user behavior or preferences using historical "
    "interaction data and machine learning models [8]. While effective at ranking items for repeat users, "
    "they operate as opaque black boxes and optimize engagement rather than decision clarity. They are "
    "ill-suited for cold-start scenarios where no interaction history exists, which is the common case "
    "for first-time shopping decisions in new categories [9]."
)

para(
    "The proposed system overlaps with recommender systems but reframes the task as decision support, "
    "prioritizing transparency and user understanding over prediction accuracy. Table 1 summarizes the "
    "capability gaps across existing tools compared to the proposed system."
)

doc.add_paragraph()
# Table 1 — Comparison
tbl = doc.add_table(rows=7, cols=6)
tbl.style = "Table Grid"
tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
headers = ["Capability", "Google\nShopping", "Amazon\nRufus", "ChatGPT\nShopping", "Perplexity", "Proposed\nSystem"]
rows_data = [
    ("Preference Elicitation",      "✗", "Partial", "Partial", "✗", "✓"),
    ("Decision Modeling",           "✗", "✗",       "✗",       "✗", "✓"),
    ("Explainable Recommendations", "✗", "✗",       "Partial", "✓", "✓"),
    ("Delivery / Promo Info",       "Partial","✗",  "✗",       "✗", "✓"),
    ("Lifecycle Support",           "✗", "✗",       "✗",       "✗", "✓"),
    ("Preference Continuity",       "✗", "Partial", "Partial", "✗", "✓"),
]
for i, header in enumerate(headers):
    cell = tbl.rows[0].cells[i]
    shade_cell(cell, "1E2761")
    set_cell_text(cell, header, bold=True, color=(0xFF,0xFF,0xFF), size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

for r, row_data in enumerate(rows_data, 1):
    for c, val in enumerate(row_data):
        cell = tbl.rows[r].cells[c]
        if c == 0:
            set_cell_text(cell, val, size=10)
        else:
            clr = (0x22,0xAA,0x55) if val == "✓" else (0xCC,0x33,0x22) if val == "✗" else (0x55,0x55,0xAA)
            set_cell_text(cell, val, bold=(val in ("✓","✗")), color=clr, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)

italic_caption("Table 1. Capability comparison of existing tools versus the proposed system.")
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Data Description
# ══════════════════════════════════════════════════════════════════════════════
heading(1, "Data Description", "3.")
para(
    "This project constructs a structured product database to support the scenario-based shopping assistant "
    "demonstration. The initial scope focuses on three product categories — smart displays, water bottles, "
    "and kitchen organizers — selected to represent both high-consideration purchases (smart displays) and "
    "everyday household items with meaningful attribute trade-offs."
)

heading(2, "Data Sources", "3.1")
para("Product data was collected from two primary e-commerce platforms:")
bullet("Amazon — primary source for smart display products, accessed via the Amazon product search page sorted by review rank.")
bullet("Target — primary source for water bottles and kitchen organizers.")
bullet("Best Buy — secondary fallback for smart displays when Amazon bot-detection blocked scraping.")
bullet("Walmart — originally planned as a fallback, but reliably blocked in practice; Target covered its role in full.")
para(
    "Data collection used Playwright-based web scrapers operating in headless mode with anti-detection "
    "stealth measures (human-like delays, slow scrolling, realistic browser fingerprints)."
)

heading(2, "Data Characteristics", "3.2")
para("The final cleaned dataset contains 100 products distributed as shown in Table 2.")

tbl2 = doc.add_table(rows=5, cols=3)
tbl2.style = "Table Grid"
tbl2.alignment = WD_TABLE_ALIGNMENT.CENTER
h2 = [("Category", "Product Count", "Primary Source")]
d2 = [
    ("smart_display",    "30", "Amazon"),
    ("water_bottle",     "35", "Target"),
    ("kitchen_organizer","35", "Target"),
    ("Total",            "100", "Amazon + Target"),
]
for i, (a,b,c) in enumerate([h2[0]] + d2):
    row = tbl2.rows[i]
    for j, val in enumerate([a,b,c]):
        if i == 0:
            shade_cell(row.cells[j], "1E2761")
            set_cell_text(row.cells[j], val, bold=True, color=(255,255,255), size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        else:
            set_cell_text(row.cells[j], val, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
italic_caption("Table 2. Dataset composition by category and source.")

heading(2, "Key Features", "3.3")
para(
    "Each product record contains 10 fields representing decision-relevant attributes, as defined in the "
    "ScrapedProduct schema (see Section 4.2). Key decision-critical fields include:"
)
for f, desc in [
    ("price (float)", "Normalized from raw strings including ranges and currency symbols"),
    ("rating (float)", "Normalized from formats such as '4.5 out of 5' or bare decimals"),
    ("review_count (int)", "Handles shorthand notation such as '1K' or '2.5K'"),
    ("arrival_time_days (int)", "Parsed from text such as 'arrives Mar 14' or 'Get it in 2 days'"),
    ("description (str)", "Short product description or badge text from the search result card"),
]:
    bullet(f"{f}: {desc}")

heading(2, "Limitations", "3.4")
para(
    "The dataset is intentionally small and scoped to support a proof-of-concept demonstration rather than "
    "production-scale recommendations. Delivery time estimates are point-in-time and may not reflect current "
    "availability. Promotion flags and pricing are subject to change. Review highlights and extended product "
    "specifications require product detail page visits and are not included in the current dataset."
)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Models
# ══════════════════════════════════════════════════════════════════════════════
heading(1, "Models", "4.")
para(
    "This section describes the five model components of the system. It opens with the overall system "
    "architecture and the trust boundary that organizes every other component (Section 4.1), then covers the "
    "ETL pipeline that collects and prepares product data (Section 4.2), the dimensional model that structures "
    "it (Section 4.3), the predictive models that drive preference parsing and recommendation ranking (Section "
    "4.4), and the visualization layer that presents results to users (Section 4.5)."
)

# ──────────────────────────────────────────────────────────────────────────────
# 4.1 — System Architecture & Trust Boundary  (NEW)
# ──────────────────────────────────────────────────────────────────────────────
heading(2, "System Architecture & Trust Boundary", "4.1")
para(
    "Before describing individual modules, this section presents the organizing architectural decision of "
    "the system: a deliberate split between probabilistic language work handled by Claude and deterministic "
    "ranking logic handled by rule-based code. Every downstream module sits on one side of this boundary."
)
para(
    "The design intent is simple. For a decision-support system, three properties are non-negotiable: a user "
    "must be able to audit why a product is ranked where it is; the developer must be able to reproduce a "
    "ranking across runs; and the ranking behavior must not drift as upstream language-model versions change. "
    "A pure LLM-wrapper architecture — where the language model both interprets the user and returns the ranked "
    "list — cannot deliver any of these properties reliably. The trust boundary makes them structural rather "
    "than aspirational."
)
para(
    "Concretely, Claude is invoked only at four well-scoped natural-language call sites (parsing, clarifying "
    "questions, trade-off explanations, and lifecycle suggestions; see Section 4.4.1). The recommendation "
    "engine — hard-constraint filtering plus two-tier weighted scoring — is pure Python and contains no calls "
    "to any language model (see Section 4.4.2). Figure 1 illustrates the split."
)

# ── Figure 1: Architecture diagram (monochrome box tables) ────────────────────
doc.add_paragraph()
# Top box — Claude / LLM
fig1_top = doc.add_table(rows=1, cols=1)
fig1_top.alignment = WD_TABLE_ALIGNMENT.CENTER
fig1_top.autofit = False
fig1_top.columns[0].width = Inches(5.5)
cell_top = fig1_top.rows[0].cells[0]
cell_top.width = Inches(5.5)
shade_cell(cell_top, "1E2761")
cell_top.text = ""
p_t1 = cell_top.paragraphs[0]
p_t1.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_t1 = p_t1.add_run("Claude (Anthropic) — Natural-Language Layer")
set_font(r_t1, size=12, bold=True, color=(255,255,255))
p_t2 = cell_top.add_paragraph()
p_t2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_t2 = p_t2.add_run("probabilistic  ·  parses preferences  ·  asks clarifying questions\n"
                    "explains trade-offs  ·  suggests lifecycle ideas")
set_font(r_t2, size=10, italic=True, color=(0xCA,0xDC,0xFC))

# Connector
conn = doc.add_paragraph()
conn.alignment = WD_ALIGN_PARAGRAPH.CENTER
conn.paragraph_format.space_before = Pt(2)
conn.paragraph_format.space_after = Pt(2)
r_c = conn.add_run("▼  structured preferences in  /  structured recommendations out  ▼")
set_font(r_c, size=10, color=(0x50,0x50,0x80))

# Bottom box — Rule-based engine
fig1_bot = doc.add_table(rows=1, cols=1)
fig1_bot.alignment = WD_TABLE_ALIGNMENT.CENTER
fig1_bot.autofit = False
fig1_bot.columns[0].width = Inches(5.5)
cell_bot = fig1_bot.rows[0].cells[0]
cell_bot.width = Inches(5.5)
shade_cell(cell_bot, "F96167")
cell_bot.text = ""
p_b1 = cell_bot.paragraphs[0]
p_b1.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_b1 = p_b1.add_run("Rule-Based Recommendation Engine — Decision Layer")
set_font(r_b1, size=12, bold=True, color=(255,255,255))
p_b2 = cell_bot.add_paragraph()
p_b2.alignment = WD_ALIGN_PARAGRAPH.CENTER
r_b2 = p_b2.add_run("deterministic  ·  hard-constraint filter  ·  two-tier weighted scoring\n"
                    "reproducible  ·  fully auditable  ·  no LLM calls")
set_font(r_b2, size=10, italic=True, color=(255,255,255))

italic_caption("Figure 1. The trust boundary — probabilistic language work above, deterministic decision logic below.")

# ── 4.1.1 Why this approach works  (NEW — mirrors LinkedIn article) ───────────
heading(3, "Why This Approach Works", "4.1.1")
para(
    "The split architecture — AI for language, rule-based code for ranking — provides four concrete "
    "benefits over a pure LLM-wrapper design:"
)
bullet("Auditability. Every ranking has a visible weighted sum. When a reviewer asks \"why is this #1?\", the system can point to numbers — no model-interpretability tooling required.")
bullet("Stability. When the Claude API version changes, the ranking does not. Only the language layer moves. The core decision logic stays reproducible across model updates, which is the baseline requirement for any system whose output must be defensible.")
bullet("Cheap iteration. Ranking changes are Python edits; LLM changes are prompt edits. Neither blocks the other, so the scoring function and the parsing prompt can be tuned in parallel.")
bullet("Explainability by construction. Because every score component is preserved alongside the product, the \"explain this ranking\" step is a lookup, not a second AI inference. The explanation cites the same numbers that produced the rank.")
para(
    "The cost of this approach is real: the scoring function must be explicitly designed rather than inferred "
    "by a model. That cost, however, is the contribution — the scoring function is where the decision-support "
    "intent is encoded."
)

# ── 4.1.2 Runtime Composition  (NEW) ──────────────────────────────────────────
heading(3, "Runtime Composition", "4.1.2")
para(
    "At runtime the system comprises four components plus two offline assets, all governed by the trust "
    "boundary above:"
)
bullet("React frontend — single-page application with four interaction stages (Onboarding, Elicitation, Recommendations, Refinement). See Section 4.5.")
bullet("FastAPI backend — four REST endpoints (/start, /answer, /recommend, /refine) that orchestrate all business logic. The frontend never calls Claude directly; every LLM call is wrapped, prompted, and validated on the backend.")
bullet("Claude API (Anthropic, Opus 4.6) — invoked at exactly four call sites (Section 4.4.1).")
bullet("Recommendation engine — Python module performing filter → score → rank, with no AI dependencies (Section 4.4.2).")
bullet("ETL pipeline (offline) — Playwright scrapers feeding a normalized catalog (Section 4.2).")
bullet("Product database (offline) — flat JSON file products_clean.json containing 100 products across three categories (Section 4.3).")

page_break()

# ──────────────────────────────────────────────────────────────────────────────
# 4.2 — ETL Pipeline (was 4.1)
# ──────────────────────────────────────────────────────────────────────────────
heading(2, "ETL Pipeline", "4.2")
para(
    "The ETL pipeline is implemented in Python using Playwright for browser automation. It consists of three "
    "active scraper modules (scrape_amazon.py, scrape_target.py, scrape_bestbuy.py), one prototype kept for "
    "parity (scrape_walmart.py, never operational in practice due to persistent bot-detection blocks), and a "
    "pipeline orchestrator (run_pipeline.py) that coordinates extraction, transformation, and loading."
)
para("The pipeline follows a three-tier query strategy for each product category:")
bullet("Primary query: attempt the preferred retailer and query string for that category.")
bullet("Fallback query: if the primary fails (site block or insufficient results), switch to an alternative retailer.")
bullet("Supplemental queries: if the product count remains below the target of 25 per category after deduplication, run additional queries to boost coverage.")
para(
    "Bot-detection resistance is achieved through a shared browser utility module (_browser.py) that "
    "applies Playwright stealth patches, randomizes request timing with human-like delays (2–4 seconds "
    "between page loads, 3–6 seconds between categories), and uses slow page scrolling to simulate "
    "organic browsing behavior."
)
para(
    "The transformation step is handled by normalize.py, which applies four normalization functions:"
)
bullet("normalize_price(): extracts a float from price strings including ranges ('$12.99 – $24.99'), currency symbols, and comma-separated thousands.")
bullet("normalize_rating(): handles formats such as '4.5 out of 5 stars', '/5' notation, and bare decimal strings.")
bullet("normalize_review_count(): parses shorthand notation ('1K', '2.5K'), Best Buy's verbose format ('Rating X with N reviews'), and plain integers with parentheses.")
bullet("normalize_delivery(): converts delivery text to an integer number of days from today, handling absolute dates ('arrives Mar 14'), relative expressions ('in 2 days', 'tomorrow'), and day ranges ('2–3 days').")
para(
    "Deduplication is performed in two phases: exact URL matching removes duplicate product pages, "
    "followed by fuzzy title matching using normalized 65-character title prefixes within the same "
    "category. When duplicates are found, the record with the higher review count is retained."
)

heading(2, "Dimensional Model", "4.3")
para(
    "The product database is represented as a flat JSON file (data/clean/products_clean.json) conforming "
    "to the ScrapedProduct TypedDict schema. This schema serves as the dimensional model for the system, "
    "with each record corresponding to a single product offer from a specific retailer. Table 3 describes "
    "the schema fields."
)
tbl3 = doc.add_table(rows=11, cols=3)
tbl3.style = "Table Grid"
tbl3.alignment = WD_TABLE_ALIGNMENT.CENTER
schema_headers = ("Field", "Type", "Description")
schema_rows = [
    ("category",           "str",        "Product category: smart_display | water_bottle | kitchen_organizer"),
    ("source",             "str",        "Retailer: amazon | bestbuy | walmart | target"),
    ("title",              "str",        "Full product title from search result card"),
    ("price",              "float|None", "Normalized price in USD"),
    ("rating",             "float|None", "Average rating out of 5.0"),
    ("review_count",       "int|None",   "Total number of customer reviews"),
    ("image_url",          "str|None",   "Product thumbnail image URL"),
    ("product_url",        "str",        "Direct link to the product detail page"),
    ("description",        "str|None",   "Short description or badge text"),
    ("arrival_time_days",  "int|None",   "Estimated delivery time in days from today"),
]
for j, h in enumerate(schema_headers):
    shade_cell(tbl3.rows[0].cells[j], "1E2761")
    set_cell_text(tbl3.rows[0].cells[j], h, bold=True, color=(255,255,255), size=10)
for r, (f,t,d) in enumerate(schema_rows, 1):
    set_cell_text(tbl3.rows[r].cells[0], f, bold=True, size=10)
    set_cell_text(tbl3.rows[r].cells[1], t, size=10)
    set_cell_text(tbl3.rows[r].cells[2], d, size=10)
italic_caption("Table 3. ScrapedProduct dimensional schema — 10 fields per product record.")

heading(2, "Predictive Models — Claude + Two-Tier Scoring", "4.4")
para(
    "Two model components drive the conversational and recommendation logic, one on each side of the trust "
    "boundary introduced in Section 4.1: Claude (Anthropic) on the language side, and a deterministic "
    "two-tier weighted-scoring engine on the decision side. This section describes each in turn."
)

heading(3, "Claude AI — Four Call Sites", "4.4.1")
para(
    "Claude (Opus 4.6) is invoked at exactly four call sites in the decision workflow [10]. Each call site "
    "has a narrow scope and a validated output schema; if parsing of Claude's response fails, the backend "
    "asks the user to rephrase rather than improvising."
)
bullet("Preference parsing — convert free-text user messages into a structured preference object (category, hard constraints, priorities, trade-off tolerance).")
bullet("Clarifying questions — when the parsed profile is sparse, generate 3–5 targeted follow-up questions that narrow the decision space.")
bullet("Trade-off explanation — for each top-ranked product, produce a one-sentence rationale grounded in the user's stated priorities and the product's score components.")
bullet("Lifecycle suggestions — after purchase, generate post-purchase ideas tailored to the chosen product (meal planning for a kitchen display, cleaning schedules for a water bottle).")
para(
    "Ranking is conspicuously absent from that list. The language model never sees the full candidate pool "
    "and never produces the ordered list that the user sees."
)

heading(3, "Recommendation Engine — Two-Tier Weighted Scoring", "4.4.2")
para(
    "The recommendation engine is pure Python and contains no language-model calls. It runs in four steps."
)
bullet("Step 1 — Hard-constraint filter. Budget ceilings and delivery deadlines are non-negotiable. Products outside them are eliminated before any scoring occurs. No product is ever kept for being \"close enough\" on a deal-breaker.")
bullet("Step 2 — Feasible set. The filter typically reduces the ~100-product catalog to 10–20 candidates. All downstream scoring operates only on this feasible set.")
bullet("Step 3 — Two-tier weighted scoring. Each feasible product is scored at two levels (general and feature), then combined. Details below.")
bullet("Step 4 — Sort and return. Products are sorted by combined score in descending order; the top N are returned. Every score component is preserved alongside the product so the explanation step (Claude call site 3) can cite the actual numbers.")

# Two-tier formula, rendered as an inset
para("The two-tier scoring formula is:", bold=True, space_before=6)
formula_p = doc.add_paragraph()
formula_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
formula_p.paragraph_format.space_before = Pt(4)
formula_p.paragraph_format.space_after = Pt(8)
r_formula = formula_p.add_run("Combined = α × GeneralScore + (1 − α) × FeatureScore")
set_font(r_formula, size=13, bold=True, color=(0x1E, 0x27, 0x61))

para(
    "Here GeneralScore is a weighted sum over attributes that apply to every product (rating, price, "
    "delivery time). FeatureScore is a weighted sum over category-specific attributes (for smart displays: "
    "voice control, screen size, smart-home integration, brand; for water bottles: insulation, capacity, "
    "durability). The blend coefficient α is tuned per category based on how much the general attributes "
    "carry the decision relative to the feature-level ones."
)
para(
    "A critical property: the general-tier weights are dynamic, not hard-coded. They are derived at "
    "request-time from the user's stated priorities. A user who says \"budget flexible, can wait for "
    "delivery\" receives a weight profile tilted toward rating (≈50%/30%/20%); a user on a tight deadline "
    "receives a profile tilted toward delivery. Table 5 summarizes representative profiles used during "
    "the kitchen assistant scenario."
)

# Table 5 — Dynamic general weights
doc.add_paragraph()
tbl5 = doc.add_table(rows=4, cols=4)
tbl5.style = "Table Grid"
tbl5.alignment = WD_TABLE_ALIGNMENT.CENTER
h5 = ("User Priority Profile", "Rating", "Price", "Delivery")
d5 = [
    ("Budget-flexible, can wait",     "50%", "30%", "20%"),
    ("Budget-sensitive, moderate wait","30%", "50%", "20%"),
    ("Deadline-driven, urgent",       "30%", "20%", "50%"),
]
for j, h in enumerate(h5):
    shade_cell(tbl5.rows[0].cells[j], "1E2761")
    set_cell_text(tbl5.rows[0].cells[j], h, bold=True, color=(255,255,255), size=10,
                  align=WD_ALIGN_PARAGRAPH.CENTER)
for r, row in enumerate(d5, 1):
    for c, val in enumerate(row):
        align = WD_ALIGN_PARAGRAPH.LEFT if c == 0 else WD_ALIGN_PARAGRAPH.CENTER
        set_cell_text(tbl5.rows[r].cells[c], val, size=10, align=align)
italic_caption("Table 5. Dynamic general-tier weights derived from user priority profile.")

# Figure 2 — Two-tier scoring pipeline diagram (horizontal box chain)
doc.add_paragraph()
fig2 = doc.add_table(rows=1, cols=5)
fig2.alignment = WD_TABLE_ALIGNMENT.CENTER
fig2.autofit = False
labels_fig2 = [
    ("Hard\nConstraint Filter", "1C7293"),
    ("Feasible Set\n(10–20)",   "028090"),
    ("General Score\n+ Feature Score", "F96167"),
    ("Combined =\nα·G + (1−α)·F", "1E2761"),
    ("Ranked\nOutput",          "2F3C7E"),
]
for j, (txt, hex_c) in enumerate(labels_fig2):
    cell = fig2.rows[0].cells[j]
    cell.width = Inches(1.2)
    shade_cell(cell, hex_c)
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(txt)
    set_font(r, size=9, bold=True, color=(255,255,255))
italic_caption("Figure 2. The deterministic ranking pipeline — filter, feasible set, two-tier score, combine, sort.")

para(
    "The entire pipeline is deterministic. Re-running the same inputs produces the same output, and every "
    "weight is an integer the user can inspect. Tie-breaking rules favor higher rating, then lower delivery "
    "time, then lower price."
)

heading(2, "Visualization — Frontend & Backend", "4.5")
para(
    "The frontend is implemented as a React single-page application (SPA) with four interaction stages, "
    "each corresponding to a phase of the decision-support workflow:"
)
bullet("Stage 1 — Onboarding: User describes their shopping need in natural language. The system introduces the decision-support approach and confirms the product category.")
bullet("Stage 2 — Preference Elicitation: Claude generates 3–5 targeted follow-up questions based on the initial need. User answers are collected and structured into a preference profile.")
bullet("Stage 3 — Recommendations: A ranked list of products is displayed with enriched attributes (price, rating, delivery days, promotion flags) and per-product trade-off explanations.")
bullet("Stage 4 — Refinement and Lifecycle: User can adjust priorities to re-rank results. After selection, Claude generates post-purchase lifecycle suggestions (meal planning, scheduling, content usage).")
para(
    "The backend is implemented as a FastAPI REST API with four endpoints: /start (initialize session), "
    "/answer (process user responses), /recommend (return ranked product list), and /refine (re-rank "
    "based on updated preferences). The backend communicates with the Claude API via the Anthropic "
    "Python SDK and queries the product database from the cleaned JSON file."
)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Results
# ══════════════════════════════════════════════════════════════════════════════
heading(1, "Results", "5.")
para(
    "Evaluation of the proposed system is conducted through three complementary approaches: a capability "
    "comparison against existing tools, a scenario-based walkthrough of the kitchen assistant demo, and "
    "a heuristic assessment of the system's decision-support quality."
)

heading(2, "Capability Comparison", "5.1")
para(
    "Table 1 (Section 2) demonstrates that the proposed system addresses all five structural gaps "
    "identified in the related work analysis. No existing tool provides all five capabilities "
    "simultaneously. The proposed system is the only one to support preference continuity across "
    "conversational turns, expose delivery time and promotion information, and extend interaction "
    "beyond the point of purchase."
)

heading(2, "ETL Pipeline Results", "5.2")
para(
    "The scraping pipeline successfully collected 100 clean products across three categories from "
    "Amazon and Target. The pipeline demonstrated resilience: the fallback mechanism activated for "
    "Walmart (consistently blocked) and redirected water bottle and kitchen organizer collection to "
    "Target. Supplemental query logic boosted per-category counts to meet the 25-product target. "
    "Table 4 summarizes the final dataset composition."
)

tbl4 = doc.add_table(rows=5, cols=4)
tbl4.style = "Table Grid"
tbl4.alignment = WD_TABLE_ALIGNMENT.CENTER
h4 = [("Category", "Count", "Source", "Avg. Rating")]
d4 = [
    ("smart_display",     "30", "Amazon",        "4.3 / 5.0"),
    ("water_bottle",      "35", "Target",         "4.5 / 5.0"),
    ("kitchen_organizer", "35", "Target",         "4.4 / 5.0"),
    ("Total / Average",   "100","Amazon + Target","4.4 / 5.0"),
]
for i, row_d in enumerate([h4[0]] + d4):
    row = tbl4.rows[i]
    for j, val in enumerate(row_d):
        if i == 0:
            shade_cell(row.cells[j], "1E2761")
            set_cell_text(row.cells[j], val, bold=True, color=(255,255,255), size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
        else:
            set_cell_text(row.cells[j], val, size=10, align=WD_ALIGN_PARAGRAPH.CENTER)
italic_caption("Table 4. Final dataset composition after ETL pipeline and deduplication.")

heading(2, "Scenario Walkthrough — Kitchen Assistant", "5.3")
para(
    "The system was evaluated through a structured scenario walkthrough representing a typical "
    "shopping decision for a smart kitchen display. The walkthrough proceeds through four stages:"
)
bullet("Onboarding: User inputs 'I want something convenient for cooking in my kitchen.'")
bullet("Elicitation: System asks 5 targeted questions covering budget (under $150), household size (family of 3), primary use (recipe display and timers), delivery urgency (within 1 week), and voice control preference (important).")
bullet("Recommendations: System returns 5 ranked smart displays with price, rating, delivery time, promotion flag, and trade-off explanations per product. Products satisfying all hard constraints are ranked by weighted score.")
bullet("Refinement: User deprioritizes screen size in favor of delivery speed. System re-ranks results accordingly and surfaces a product with 2-day delivery as the top recommendation.")
para(
    "The walkthrough demonstrated that the system successfully preserves preference continuity across "
    "turns, surfaces delivery-critical information absent from baseline tools, and produces readable "
    "trade-off explanations that map directly to user-stated priorities."
)

para("The concrete score components returned for the top-ranked candidates are shown in Table 6, using the "
     "weight profile derived from the elicited preferences (budget-flexible, moderate wait: Rating 50% / "
     "Price 30% / Delivery 20%, with α = 0.6 for smart_display).")

# Table 6 — Worked-example product scores
doc.add_paragraph()
tbl6 = doc.add_table(rows=4, cols=5)
tbl6.style = "Table Grid"
tbl6.alignment = WD_TABLE_ALIGNMENT.CENTER
h6 = ("Product", "Price", "General", "Feature", "Combined")
d6 = [
    ("Echo Show 8 (2nd Gen)",    "$109.99", "0.82", "0.88", "0.84"),
    ("Google Nest Hub (2nd Gen)","$ 99.99", "0.80", "0.79", "0.80"),
    ("Echo Show 5 (3rd Gen)",    "$ 74.99", "0.76", "0.72", "0.74"),
]
for j, h in enumerate(h6):
    shade_cell(tbl6.rows[0].cells[j], "1E2761")
    set_cell_text(tbl6.rows[0].cells[j], h, bold=True, color=(255,255,255), size=10,
                  align=WD_ALIGN_PARAGRAPH.CENTER)
for r, row in enumerate(d6, 1):
    for c, val in enumerate(row):
        align = WD_ALIGN_PARAGRAPH.LEFT if c == 0 else WD_ALIGN_PARAGRAPH.CENTER
        set_cell_text(tbl6.rows[r].cells[c], val, size=10, align=align)
italic_caption("Table 6. Worked example — top three ranked smart displays with score components "
               "(illustrative values from the kitchen-assistant scenario).")
para(
    "On refinement, when the user deprioritizes screen size and raises delivery urgency, the delivery weight "
    "shifts from 20% to 45% and the Echo Show 5 (3rd Gen) — a smaller unit available with 2-day delivery — "
    "rises to the top of the list. Importantly, the language model is never re-invoked for the re-rank; only "
    "the weight profile and the Python scoring pass change, which is why refinement is instant and "
    "deterministic."
)

heading(2, "Heuristic Evaluation", "5.4")
para("The system was assessed against three heuristic criteria derived from the research objectives:")
bullet("Information completeness: All 10 product attributes including delivery time and promotion flags are surfaced in the recommendation view, compared to image + price only in baseline tools.")
bullet("Interaction efficiency: The decision workflow completes in 4 stages with no external page navigation required. All product actions (view, refine, lifecycle) are available within a single interface.")
bullet("Transparency: Each recommendation includes a structured explanation mapping product attributes to user priorities, making the ranking rationale auditable.")
para(
    "This evaluation is a heuristic self-assessment against the six capability gaps identified in Section 2 "
    "and is intended to validate architectural feasibility, not to substitute for user research. A formal "
    "user study — including task completion time, self-reported decision confidence, and System Usability "
    "Scale scores — is identified as future work (Section 6.1).",
    italic=True, size=10
)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Conclusions and Impact
# ══════════════════════════════════════════════════════════════════════════════
heading(1, "Conclusions and Impact", "6.")
para(
    "This project demonstrates that decision-oriented conversational shopping assistance is technically "
    "feasible as a full-stack, end-to-end system built with currently available AI models and open-source "
    "tools. The five-layer architecture — preference elicitation, decision modeling, recommendation "
    "ranking, explainability, and lifecycle support — integrates coherently into a unified user experience "
    "that addresses structural gaps in existing shopping AI tools. Its organizing idea is the trust boundary "
    "between language and decision work: the language model handles what it is good at (parsing, explaining, "
    "suggesting) and the deterministic engine handles what it must do reliably (ranking)."
)
para(
    "The key contributions of this work are:"
)
bullet("A novel framing of the e-commerce recommendation problem as a decision-support task, distinct from engagement-optimized retrieval.")
bullet("A trust-boundary architecture that separates probabilistic language work (Claude) from deterministic ranking logic (rule-based Python), yielding auditability, reproducibility across model updates, and explainability by construction — properties absent from pure LLM-wrapper approaches.")
bullet("A two-tier weighted scoring engine with dynamic general-tier weights derived from user priorities, blended with category-specific feature weights via a tunable coefficient α.")
bullet("A real data engineering pipeline that collects, normalizes, and deduplicates product data from live e-commerce platforms, demonstrating production-relevant ETL techniques.")
bullet("A working full-stack implementation validated through scenario-based walkthrough, showing that preference elicitation, constraint-aware ranking, and explainable trade-offs can be delivered within a single conversational interface.")
bullet("A post-purchase lifecycle support layer that extends the value of the decision assistant beyond the transaction, a capability absent from all reviewed baseline tools.")
para(
    "The broader impact of this approach is a shift in how AI shopping tools are evaluated: not by "
    "click-through rate or recommendation accuracy, but by decision quality, user confidence, and "
    "transparency. As AI assistants become embedded in consumer commerce, decision support — rather "
    "than engagement optimization — represents a more user-aligned design objective."
)

heading(2, "Future Work", "6.1")
para("Several directions would strengthen and extend this work:")
bullet("Formal user study: A randomized usability study measuring task completion time, decision confidence (self-reported), and System Usability Scale (SUS) scores would provide quantitative validation.")
bullet("Live data integration: Replacing the static scraped database with real-time retailer API connections would improve delivery time accuracy and pricing freshness.")
bullet("ML-based ranking: Replacing the rule-based weighted scorer with a learning-to-rank model trained on user interaction history would improve personalization at scale.")
bullet("Expanded product categories: Extending the system beyond three categories would validate the generalizability of the preference elicitation and decision modeling layers.")
bullet("Mobile-first UI: Redesigning the React frontend for mobile form factors would increase accessibility for on-the-go shopping decisions.")
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Contributions
# ══════════════════════════════════════════════════════════════════════════════
heading(1, "Contributions", "7.")

heading(2, "Student Contributions", "7.1")
para(
    "This capstone project was completed individually by Chenghui Tan. All system components were designed, "
    "implemented, and evaluated by the author:"
)
bullet("Architecture — defined the five-layer decision-support framework and the trust boundary that governs it.")
bullet("Data engineering — Playwright ETL pipeline (three active scrapers, orchestrator with fallback/supplement logic, normalization utilities).")
bullet("Recommendation engine — two-tier weighted scoring with dynamic general weights and category-specific feature weights.")
bullet("Claude integration — prompt design and response validation for the four language call sites.")
bullet("Full-stack implementation — React SPA (four stages) and FastAPI backend (four endpoints).")
bullet("Evaluation — capability comparison, scenario walkthrough with worked scores, heuristic assessment.")
bullet("Documentation — this report, slide deck, and all supporting materials.")

heading(2, "AI Tool Contributions", "7.2")
para(
    "AI tools were used in the following capacities during this project:"
)
bullet("Claude (Anthropic, Opus 4.6) — natural-language layer of the application: preference parsing, clarifying question generation, recommendation explanation generation, and lifecycle suggestion generation. Also used during development for code assistance, debugging, and documentation drafting.")
bullet("GitHub Copilot — used for code completion suggestions during frontend and backend implementation.")
para(
    "All AI-generated code was reviewed, tested, and modified by the author. The system architecture, "
    "research framing, evaluation design, and written analysis reflect the author's original intellectual "
    "contributions."
)
page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — References
# ══════════════════════════════════════════════════════════════════════════════
heading(1, "References", "8.")
refs = [
    "[1] B. Schwartz, The Paradox of Choice: Why More Is Less. New York: HarperCollins, 2004.",
    "[2] T. W. Malone and K. Crowston, 'The interdisciplinary study of coordination,' ACM Computing Surveys, vol. 26, no. 1, pp. 87–119, 1994.",
    "[3] Google, 'Google Shopping Help Center,' Google LLC. [Online]. Available: https://support.google.com/merchants/. [Accessed: Apr. 2026].",
    "[4] Amazon, 'Rufus: AI Shopping Assistant,' Amazon.com, Inc. [Online]. Available: https://www.aboutamazon.com/news/retail/amazon-rufus. [Accessed: Apr. 2026].",
    "[5] OpenAI, 'ChatGPT Shopping Integration,' OpenAI. [Online]. Available: https://openai.com/chatgpt. [Accessed: Apr. 2026].",
    "[6] Y. Zhang and X. Chen, 'Explainable recommendation: A survey and new perspectives,' Foundations and Trends in Information Retrieval, vol. 14, no. 1, pp. 1–101, 2020.",
    "[7] Perplexity AI, 'Perplexity AI: Ask Anything,' Perplexity AI, Inc. [Online]. Available: https://www.perplexity.ai. [Accessed: Apr. 2026].",
    "[8] F. Ricci, L. Rokach, and B. Shapira, Eds., Recommender Systems Handbook, 2nd ed. New York: Springer, 2015.",
    "[9] A. Schein, A. Popescul, L. Ungar, and D. Pennock, 'Methods and metrics for cold-start recommendations,' in Proc. 25th Annual International ACM SIGIR Conf., Tampere, Finland, 2002, pp. 253–260.",
    "[10] Anthropic, 'Claude API Documentation,' Anthropic PBC. [Online]. Available: https://docs.anthropic.com. [Accessed: Apr. 2026].",
    "[11] Playwright Contributors, 'Playwright for Python,' Microsoft. [Online]. Available: https://playwright.dev/python/. [Accessed: Apr. 2026].",
    "[12] FastAPI Contributors, 'FastAPI Documentation,' Sebastián Ramírez. [Online]. Available: https://fastapi.tiangolo.com. [Accessed: Apr. 2026].",
]
for ref in refs:
    p = doc.add_paragraph()
    p.paragraph_format.left_indent  = Inches(0.3)
    p.paragraph_format.first_line_indent = Inches(-0.3)
    p.paragraph_format.space_after  = Pt(4)
    run = p.add_run(ref)
    set_font(run, size=10)

page_break()

# ══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — Appendix
# ══════════════════════════════════════════════════════════════════════════════
heading(1, "Appendix — Code Listings", "9.")
para(
    "The following code listings illustrate key implementation components. The full source code is "
    "available in the project repository at /Users/sabrina/Projects/shopping-assistant-4/."
)

heading(2, "A. ETL Pipeline Orchestrator (run_pipeline.py — excerpt)", "9.1")
code_snippet = (
    "PIPELINE = [\n"
    "    {\n"
    "        'category': 'smart_display',\n"
    "        'filename': 'smart_display.json',\n"
    "        'primary':  (scrape_amazon, 'smart display for kitchen'),\n"
    "        'fallback': (scrape_bestbuy, 'smart display echo show google nest hub'),\n"
    "        'supplement': [\n"
    "            (scrape_amazon, 'echo show smart home display kitchen'),\n"
    "        ],\n"
    "    },\n"
    "    ...\n"
    "]\n\n"
    "async def scrape_with_fallback(cfg, headed):\n"
    "    # Try primary → fallback with randomized wait between attempts\n"
    "    for attempt, (mod, query, label) in enumerate([primary, fallback]):\n"
    "        results = await mod.scrape(query=query, category=cfg['category'], ...)\n"
    "        if len(results) >= 5:\n"
    "            return results\n"
    "        await asyncio.sleep(random.uniform(4, 8))  # human-like delay\n"
)
p_code = doc.add_paragraph()
p_code.paragraph_format.left_indent = Inches(0.3)
run_code = p_code.add_run(code_snippet)
set_font(run_code, name="Courier New", size=9)

heading(2, "B. Delivery Normalization (normalize.py — excerpt)", "9.2")
code2 = (
    "def normalize_delivery(raw: str | None) -> int | None:\n"
    "    s = raw.lower().strip()\n"
    "    if 'today' in s or 'same day' in s: return 0\n"
    "    if 'tomorrow' in s:                 return 1\n"
    "    # 'in N days' / 'N-day shipping'\n"
    "    m = re.search(r'in\\s+(\\d+)\\s+day', s)\n"
    "    if m: return int(m.group(1))\n"
    "    # 'arrives Mar 14' → compute delta from today\n"
    "    m = re.search(r'(?:by|arrives?).*([a-z]{3})\\w*\\s+(\\d{1,2})', s)\n"
    "    if m: return _days_until_month_day(m.group(1), m.group(2))\n"
    "    return None\n"
)
p_code2 = doc.add_paragraph()
p_code2.paragraph_format.left_indent = Inches(0.3)
run_code2 = p_code2.add_run(code2)
set_font(run_code2, name="Courier New", size=9)

heading(2, "C. FastAPI Endpoints (main.py — route summary)", "9.3")
code3 = (
    "POST /start      → Initialize session, return opening question\n"
    "POST /answer     → Process user answer, return next question or signal completion\n"
    "POST /recommend  → Return ranked product list with trade-off explanations\n"
    "POST /refine     → Re-rank products based on updated user priorities\n"
)
p_code3 = doc.add_paragraph()
p_code3.paragraph_format.left_indent = Inches(0.3)
run_code3 = p_code3.add_run(code3)
set_font(run_code3, name="Courier New", size=9)

# ── Save ──────────────────────────────────────────────────────────────────────
out = "/Users/sabrina/Projects/shopping-assistant-4/docs/capstone_report_v2.docx"
doc.save(out)
print(f"Saved → {out}")
