"""
Capstone Presentation v3 — 11 slides
A Decision-Oriented Conversational Shopping Assistant
Chenghui Tan — CSUEB · April 2026

Tier 1+2+3 rework:
  · Trust-boundary becomes the organizing idea (new Slide 5)
  · Claude (Opus 4.6) corrected from "Sonnet"
  · α = 0.6 surfaced on algorithm slide
  · Merged Market+Competitive (was 3+4) and Conceptual+Runtime (was 6+7)
  · Supporting-stack slide replaced with focused Data Pipeline
  · Visual: tight Navy/Ice/Coral palette · Georgia headers · no accent dividers
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Palette (tightened) ───────────────────────────────────────────────────────
NAVY      = RGBColor(0x1E, 0x27, 0x61)   # AI / language side
NAVY_DEEP = RGBColor(0x12, 0x1A, 0x47)
MID_BLUE  = RGBColor(0x3A, 0x4F, 0x9B)
ICE       = RGBColor(0xCA, 0xDC, 0xFC)
ICE_DEEP  = RGBColor(0xA9, 0xC1, 0xF4)
LIGHT_BG  = RGBColor(0xF4, 0xF6, 0xFD)
PANEL_BG  = RGBColor(0xE7, 0xEC, 0xF9)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
DARK_TEXT = RGBColor(0x1A, 0x1A, 0x2E)
MUTED     = RGBColor(0x6B, 0x7A, 0xB8)
MUTED_D   = RGBColor(0x4A, 0x58, 0x90)
# Single accent — reserved for the rule-based / decision side
CORAL     = RGBColor(0xF9, 0x61, 0x67)
CORAL_D   = RGBColor(0xC9, 0x3F, 0x45)
# Sparing utility colors
GREEN_OK  = RGBColor(0x2E, 0xB8, 0x6B)
RED_NO    = RGBColor(0xE7, 0x4C, 0x3C)

HEADER_FONT = "Georgia"
BODY_FONT   = "Calibri"

W = Inches(13.33)
H = Inches(7.5)

# ── Helpers ───────────────────────────────────────────────────────────────────
def add_rect(slide, l, t, w, h, fill, line=False, line_color=None):
    s = slide.shapes.add_shape(1, l, t, w, h)
    if line and line_color is not None:
        s.line.color.rgb = line_color
        s.line.width = Pt(1.25)
    else:
        s.line.fill.background()
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    return s

def add_text(slide, text, l, t, w, h,
             bold=False, size=14, color=WHITE,
             align=PP_ALIGN.LEFT, wrap=True, italic=False,
             font=BODY_FONT):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.margin_left = Inches(0.04)
    tf.margin_right = Inches(0.04)
    tf.margin_top = Inches(0.02)
    tf.margin_bottom = Inches(0.02)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.bold = bold
    run.font.italic = italic
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.name = font
    return tb

def bg(slide, color):
    add_rect(slide, 0, 0, W, H, color)

def top_accent(slide, color):
    """Single thin top accent — replaces the old title-divider AI tell."""
    add_rect(slide, 0, 0, W, Inches(0.06), color)

def section_label(slide, text, color):
    add_text(slide, text.upper(),
             Inches(0.6), Inches(0.3), Inches(12), Inches(0.3),
             bold=True, size=9, color=color, font=BODY_FONT)

def slide_title(slide, text, color, size=32):
    add_text(slide, text,
             Inches(0.6), Inches(0.6), Inches(12.1), Inches(1.0),
             bold=True, size=size, color=color, font=HEADER_FONT)

def slide_num(slide, n, total=11, dark=True):
    c = MUTED if dark else ICE_DEEP
    add_text(slide, f"{n} / {total}",
             Inches(12.1), H - Inches(0.42), Inches(1.1), Inches(0.3),
             size=9, color=c, align=PP_ALIGN.RIGHT, font=BODY_FONT)

def corner_motif(slide, color):
    """Small square motif repeated on every content slide (visual through-line)."""
    add_rect(slide, Inches(0.25), Inches(0.3), Inches(0.18), Inches(0.18), color)

def icon_circle(slide, l, t, diam, fill, glyph, glyph_color=WHITE, glyph_size=14):
    """Icon-in-colored-circle motif (oval shape)."""
    s = slide.shapes.add_shape(9, l, t, diam, diam)  # 9 = oval
    s.line.fill.background()
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    add_text(slide, glyph, l, t, diam, diam,
             bold=True, size=glyph_size, color=glyph_color,
             align=PP_ALIGN.CENTER, font=BODY_FONT)

# ── Presentation ──────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = W
prs.slide_height = H
BL = prs.slide_layouts[6]
TOTAL = 11

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — Title  (DARK)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, NAVY)
add_rect(s, 0, Inches(6.7), W, Inches(0.1), CORAL)  # coral strip (boundary motif)

add_text(s, "APPLIED RESEARCH  ·  CAPSTONE PRESENTATION",
         Inches(0.7), Inches(1.3), Inches(12), Inches(0.4),
         bold=True, size=10, color=ICE)

add_text(s, "A Decision-Oriented",
         Inches(0.7), Inches(1.9), Inches(12.2), Inches(1.1),
         bold=True, size=52, color=WHITE, font=HEADER_FONT)
add_text(s, "Conversational Shopping Assistant",
         Inches(0.7), Inches(2.75), Inches(12.2), Inches(1.1),
         bold=True, size=52, color=WHITE, font=HEADER_FONT)

# Trust-boundary tagline — the organizing idea
add_rect(s, Inches(0.7), Inches(4.15), Inches(0.12), Inches(0.5), CORAL)
add_text(s, "Claude does language.  Deterministic code does ranking.",
         Inches(0.95), Inches(4.15), Inches(11.5), Inches(0.5),
         italic=True, size=18, color=ICE, font=HEADER_FONT)

add_text(s, "Preference Elicitation  ·  Explainable Recommendations  ·  Lifecycle Support",
         Inches(0.7), Inches(4.8), Inches(12), Inches(0.4),
         size=13, color=ICE_DEEP)

add_text(s, "Chenghui Tan",
         Inches(0.7), Inches(5.7), Inches(6), Inches(0.45),
         bold=True, size=16, color=WHITE, font=HEADER_FONT)
add_text(s, "California State University, East Bay  ·  April 2026",
         Inches(0.7), Inches(6.1), Inches(8), Inches(0.4),
         size=12, color=MUTED)

slide_num(s, 1, total=TOTAL, dark=False)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — The Problem  (LIGHT)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, LIGHT_BG)
top_accent(s, NAVY)
corner_motif(s, CORAL)

section_label(s, "01  ·  The Problem", NAVY)
slide_title(s, "Shopping Is a Decision Problem — Not a Search Problem", NAVY, 28)

# Left — 4 pain points as icon rows on a white card
add_rect(s, Inches(0.45), Inches(1.85), Inches(7.2), Inches(5.1), WHITE,
         line=True, line_color=ICE_DEEP)
add_text(s, "Why the Existing Model Breaks Down",
         Inches(0.65), Inches(2.0), Inches(6.9), Inches(0.4),
         bold=True, size=14, color=NAVY, font=HEADER_FONT)

problems = [
    ("1", "Cognitive Overload",
     "Users juggle every constraint and trade-off themselves."),
    ("2", "Vague, Evolving Needs",
     "People rarely know exactly what they want when they start."),
    ("3", "Preferences Get Overwritten",
     "Add a new constraint — earlier choices quietly disappear."),
    ("4", "Missing Critical Info",
     "Delivery time, promos, availability hidden or absent."),
]
for i, (num, title, desc) in enumerate(problems):
    y = Inches(2.55) + i * Inches(1.05)
    icon_circle(s, Inches(0.7), y, Inches(0.55), NAVY, num, ICE, 16)
    add_text(s, title, Inches(1.45), y + Inches(0.02),
             Inches(6.0), Inches(0.4),
             bold=True, size=13, color=NAVY, font=HEADER_FONT)
    add_text(s, desc, Inches(1.45), y + Inches(0.42),
             Inches(6.0), Inches(0.5),
             size=11, color=DARK_TEXT)

# Right — consequence framing (navy block)
add_rect(s, Inches(7.95), Inches(1.85), Inches(4.9), Inches(5.1), NAVY)
add_text(s, "The Decision Burden",
         Inches(8.15), Inches(2.05), Inches(4.6), Inches(0.5),
         bold=True, size=17, color=WHITE, font=HEADER_FONT)
add_text(s, "Falls on the user.",
         Inches(8.15), Inches(2.55), Inches(4.6), Inches(0.4),
         size=17, color=CORAL, italic=True, font=HEADER_FONT)

add_rect(s, Inches(8.15), Inches(3.25), Inches(0.08), Inches(2.7), CORAL)

consequences = [
    "Decision fatigue compounds with each new option.",
    "Users guess, settle, or abandon the purchase.",
    "Post-purchase regret — trade-offs were never visible.",
    "Trust erodes when recommendations have no rationale.",
]
for i, c in enumerate(consequences):
    add_text(s, c,
             Inches(8.35), Inches(3.3) + i * Inches(0.68),
             Inches(4.4), Inches(0.6),
             size=11, color=ICE)

# Bottom takeaway bar
add_rect(s, Inches(0.45), Inches(7.02), Inches(12.45), Inches(0.3), CORAL)
add_text(s,
         "We built a system that addresses the decision — not just the search.",
         Inches(0.45), Inches(7.02), Inches(12.45), Inches(0.3),
         bold=True, size=11, color=WHITE, align=PP_ALIGN.CENTER)

slide_num(s, 2, total=TOTAL, dark=True)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — The Landscape  (DARK)  [Merged from old 3+4]
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, NAVY)
add_rect(s, 0, 0, W, Inches(0.06), CORAL)

section_label(s, "02  ·  The Landscape", ICE)
slide_title(s, "Existing Platforms Don't Support Decisions", WHITE, 28)

# Thin platform ticker
platforms = ["Google Shopping", "Amazon Rufus", "ChatGPT Shopping", "Perplexity", "Our System"]
tw = Inches(2.42); tgap = Inches(0.08); tx0 = Inches(0.45); ty = Inches(1.7)
for i, name in enumerate(platforms):
    fill = CORAL if name == "Our System" else NAVY_DEEP
    add_rect(s, tx0 + i * (tw + tgap), ty, tw, Inches(0.4), fill)
    add_text(s, name, tx0 + i * (tw + tgap), ty + Inches(0.08),
             tw, Inches(0.3),
             bold=True, size=11, color=WHITE if name == "Our System" else ICE,
             align=PP_ALIGN.CENTER, font=HEADER_FONT)

# Capability comparison table — the evidence
col_labels = ["Capability",
              "Google\nShopping", "Amazon\nRufus",
              "ChatGPT\nShopping", "Perplexity", "Our\nSystem"]
col_w = [Inches(3.2), Inches(1.82), Inches(1.82), Inches(1.82), Inches(1.82), Inches(1.98)]
x_starts = [Inches(0.45)]
for cw in col_w[:-1]:
    x_starts.append(x_starts[-1] + cw)

row_h = Inches(0.55); header_y = Inches(2.3)

# Header row
for i, (label, x, cw) in enumerate(zip(col_labels, x_starts, col_w)):
    fill = CORAL if i == len(col_labels) - 1 else NAVY_DEEP
    add_rect(s, x, header_y, cw - Inches(0.03), row_h, fill)
    add_text(s, label, x, header_y + Inches(0.05),
             cw - Inches(0.05), row_h,
             bold=True, size=10, color=WHITE, align=PP_ALIGN.CENTER,
             font=HEADER_FONT)

rows_data = [
    ("Preference Elicitation",      "✗", "Partial", "Partial", "✗", "✓"),
    ("Decision Modeling",           "✗", "✗",       "✗",       "✗", "✓"),
    ("Explainable Recommendations", "✗", "✗",       "Partial", "✓", "✓"),
    ("Delivery / Promo Info",       "Partial","✗",  "✗",       "✗", "✓"),
    ("Preference Continuity",       "✗", "Partial", "Partial", "✗", "✓"),
    ("Lifecycle Support",           "✗", "✗",       "✗",       "✗", "✓"),
]

for r, (row_label, *vals) in enumerate(rows_data):
    y = header_y + row_h * (r + 1) + Inches(0.03)
    row_fill = NAVY_DEEP if r % 2 == 0 else RGBColor(0x22, 0x2D, 0x6E)
    add_rect(s, x_starts[0], y, col_w[0] - Inches(0.03),
             row_h - Inches(0.03), MID_BLUE)
    add_text(s, row_label, x_starts[0] + Inches(0.12), y + Inches(0.13),
             col_w[0] - Inches(0.2), row_h,
             size=11, color=WHITE)
    for j, (val, x, cw) in enumerate(zip(vals, x_starts[1:], col_w[1:]), 1):
        col_is_ours = (j == len(vals))
        cell_fill = CORAL_D if col_is_ours else row_fill
        add_rect(s, x, y, cw - Inches(0.03), row_h - Inches(0.03), cell_fill)
        c = GREEN_OK if val == "✓" else RED_NO if val == "✗" else ICE_DEEP
        if col_is_ours and val == "✓":
            c = WHITE
        add_text(s, val, x, y + Inches(0.08),
                 cw - Inches(0.03), row_h,
                 bold=(val in ("✓", "✗")), size=13, color=c,
                 align=PP_ALIGN.CENTER)

# Bottom bridge — tempered claim
add_rect(s, Inches(0.45), Inches(6.9), Inches(12.45), Inches(0.42), CORAL)
add_text(s,
         "Our system targets every gap — in a single decision-oriented flow.",
         Inches(0.45), Inches(6.95), Inches(12.45), Inches(0.35),
         bold=True, size=12, color=WHITE, align=PP_ALIGN.CENTER, font=HEADER_FONT)

slide_num(s, 3, total=TOTAL, dark=False)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — System Overview  (LIGHT)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, LIGHT_BG)
top_accent(s, NAVY)
corner_motif(s, CORAL)

section_label(s, "03  ·  System Overview", NAVY)
slide_title(s, "What the Assistant Actually Does", NAVY, 30)

clusters = [
    ("1", "Understand You",
     ["Situational context", "Smart guided Q&A", "Continuous flow"],
     "e.g.  “I need something for cooking”"),
    ("2", "Built for You",
     ["Personal AI guide", "Preference memory", "Multi-criteria model"],
     "remembers  ≤ $80  ·  3-day  ·  quiet home"),
    ("3", "Clear Results",
     ["Structured — not text heavy", "Full attributes visible", "Explainable trade-offs"],
     "shows the trade-off, not just the rank"),
]

card_w = Inches(4.05); card_h = Inches(4.7)
card_gap = Inches(0.15); card_x0 = Inches(0.5); card_y = Inches(1.7)

for i, (num, title, chips_list, example) in enumerate(clusters):
    x = card_x0 + i * (card_w + card_gap)
    # White card with subtle border
    add_rect(s, x, card_y, card_w, card_h, WHITE, line=True, line_color=ICE_DEEP)
    # Navy header band
    add_rect(s, x, card_y, card_w, Inches(0.9), NAVY)
    icon_circle(s, x + Inches(0.3), card_y + Inches(0.18),
                Inches(0.55), CORAL, num, WHITE, 16)
    add_text(s, title, x + Inches(1.0), card_y + Inches(0.26),
             card_w - Inches(1.1), Inches(0.5),
             bold=True, size=17, color=WHITE, font=HEADER_FONT)
    # Chips inside
    for j, chip_text in enumerate(chips_list):
        cy = card_y + Inches(1.2) + j * Inches(0.72)
        add_rect(s, x + Inches(0.3), cy,
                 card_w - Inches(0.6), Inches(0.55), PANEL_BG)
        add_rect(s, x + Inches(0.3), cy, Inches(0.08), Inches(0.55), CORAL)
        add_text(s, chip_text,
                 x + Inches(0.5), cy + Inches(0.11),
                 card_w - Inches(0.8), Inches(0.35),
                 bold=True, size=12, color=NAVY)
    # Example footer
    add_text(s, example,
             x + Inches(0.3), card_y + card_h - Inches(0.7),
             card_w - Inches(0.6), Inches(0.6),
             size=10, color=MUTED_D, italic=True, align=PP_ALIGN.CENTER)

# Lifecycle tag
add_rect(s, Inches(0.5), Inches(6.6), Inches(12.4), Inches(0.42), NAVY)
add_text(s, "+  Lifecycle support — value continues after the purchase.",
         Inches(0.5), Inches(6.65), Inches(12.4), Inches(0.35),
         bold=True, size=12, color=ICE, align=PP_ALIGN.CENTER, font=HEADER_FONT)

slide_num(s, 4, total=TOTAL, dark=True)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — The Trust Boundary  (DARK)  [NEW — anchor slide]
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, NAVY)
add_rect(s, 0, 0, W, Inches(0.06), CORAL)

section_label(s, "04  ·  The Core Architectural Decision", ICE)
slide_title(s, "The Trust Boundary", WHITE, 38)

add_text(s, "AI handles language.  Deterministic code handles the decision.",
         Inches(0.6), Inches(1.45), Inches(12.2), Inches(0.45),
         italic=True, size=16, color=CORAL, font=HEADER_FONT)

# Top band — AI / Language (navy-light)
AI_Y = Inches(2.1); AI_H = Inches(2.0)
add_rect(s, Inches(0.6), AI_Y, Inches(12.15), AI_H, MID_BLUE)
add_text(s, "Claude  (Opus 4.6)  —  Natural Language",
         Inches(0.85), AI_Y + Inches(0.15), Inches(11.6), Inches(0.4),
         bold=True, size=16, color=WHITE, font=HEADER_FONT)
add_text(s, "Probabilistic  ·  Translator between messy intent and structured data",
         Inches(0.85), AI_Y + Inches(0.55), Inches(11.6), Inches(0.35),
         size=11, color=ICE, italic=True)

claude_sites = [
    ("①", "Parse preferences"),
    ("②", "Clarifying questions"),
    ("③", "Explain trade-offs"),
    ("④", "Lifecycle suggestions"),
]
cs_w = Inches(2.85); cs_gap = Inches(0.1); cs_x0 = Inches(0.85)
for i, (num, label) in enumerate(claude_sites):
    cx = cs_x0 + i * (cs_w + cs_gap)
    add_rect(s, cx, AI_Y + Inches(1.05), cs_w, Inches(0.78), NAVY_DEEP)
    add_text(s, num, cx + Inches(0.15), AI_Y + Inches(1.15),
             Inches(0.4), Inches(0.5),
             bold=True, size=16, color=CORAL, font=HEADER_FONT)
    add_text(s, label, cx + Inches(0.55), AI_Y + Inches(1.24),
             cs_w - Inches(0.6), Inches(0.5),
             bold=True, size=12, color=ICE)

# The Boundary — coral strip + label
BY = Inches(4.25)
add_rect(s, Inches(0.6), BY, Inches(12.15), Inches(0.52), CORAL)
add_text(s, "▼   T R U S T    B O U N D A R Y   ▼",
         Inches(0.6), BY + Inches(0.08), Inches(12.15), Inches(0.4),
         bold=True, size=12, color=WHITE, align=PP_ALIGN.CENTER, font=HEADER_FONT)

# Bottom band — Rule-based / Decision (coral-outlined)
RB_Y = Inches(4.93); RB_H = Inches(2.0)
add_rect(s, Inches(0.6), RB_Y, Inches(12.15), RB_H, NAVY_DEEP,
         line=True, line_color=CORAL)
add_text(s, "Rule-Based Recommendation Engine  —  The Decision",
         Inches(0.85), RB_Y + Inches(0.15), Inches(11.6), Inches(0.4),
         bold=True, size=16, color=WHITE, font=HEADER_FONT)
add_text(s, "Deterministic  ·  Auditable  ·  Every weight visible  ·  Reproducible across model updates",
         Inches(0.85), RB_Y + Inches(0.55), Inches(11.6), Inches(0.35),
         size=11, color=CORAL, italic=True)

rb_sites = [
    ("①", "Hard constraint filter"),
    ("②", "Feasible set"),
    ("③", "Two-tier weighted scoring"),
    ("④", "Ranked output"),
]
for i, (num, label) in enumerate(rb_sites):
    cx = cs_x0 + i * (cs_w + cs_gap)
    add_rect(s, cx, RB_Y + Inches(1.05), cs_w, Inches(0.78), NAVY)
    add_text(s, num, cx + Inches(0.15), RB_Y + Inches(1.15),
             Inches(0.4), Inches(0.5),
             bold=True, size=16, color=CORAL, font=HEADER_FONT)
    add_text(s, label, cx + Inches(0.55), RB_Y + Inches(1.24),
             cs_w - Inches(0.6), Inches(0.5),
             bold=True, size=12, color=ICE)

slide_num(s, 5, total=TOTAL, dark=False)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — Architecture  (LIGHT)  [Merged conceptual + runtime]
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, LIGHT_BG)
top_accent(s, NAVY)
corner_motif(s, CORAL)

section_label(s, "05  ·  Architecture", NAVY)
slide_title(s, "Conceptual Layers & Runtime Components", NAVY, 28)

# ── Top band: conceptual 5-layer flow ─────────────────────────────────────────
add_text(s, "Conceptual Flow",
         Inches(0.6), Inches(1.55), Inches(6), Inches(0.35),
         bold=True, size=12, color=NAVY, font=HEADER_FONT)

layers = [
    ("1", "Preference\nElicitation"),
    ("2", "Decision\nModeling"),
    ("3", "Recommendation\n& Ranking"),
    ("4", "Explainability"),
    ("5", "Lifecycle\nSupport"),
]
lx0 = Inches(0.55); lw = Inches(2.42); lh = Inches(1.1); lgap = Inches(0.08)
ly = Inches(1.95)
for i, (num, title) in enumerate(layers):
    x = lx0 + i * (lw + lgap)
    add_rect(s, x, ly, lw, lh, NAVY)
    add_rect(s, x, ly, Inches(0.5), lh, CORAL)
    add_text(s, num, x, ly + Inches(0.3),
             Inches(0.5), Inches(0.5),
             bold=True, size=22, color=WHITE, align=PP_ALIGN.CENTER,
             font=HEADER_FONT)
    add_text(s, title, x + Inches(0.55), ly + Inches(0.2),
             lw - Inches(0.6), Inches(0.8),
             bold=True, size=12, color=WHITE, font=HEADER_FONT)
    if i < len(layers) - 1:
        add_text(s, "→", x + lw - Inches(0.02), ly + Inches(0.35),
                 lgap + Inches(0.05), Inches(0.4),
                 bold=True, size=16, color=NAVY)

# ── Bottom band: runtime tech — compact 2-row diagram ─────────────────────────
add_text(s, "Runtime Components",
         Inches(0.6), Inches(3.25), Inches(6), Inches(0.35),
         bold=True, size=12, color=NAVY, font=HEADER_FONT)

# Row 1 (top of tech): frontend → backend → Claude
R1Y = Inches(3.65); R1H = Inches(1.2)
rr_w = Inches(3.9); rr_gap = Inches(0.25)
# React
add_rect(s, Inches(0.55), R1Y, rr_w, R1H, NAVY)
add_text(s, "React Frontend", Inches(0.55), R1Y + Inches(0.12),
         rr_w, Inches(0.4),
         bold=True, size=13, color=WHITE, align=PP_ALIGN.CENTER, font=HEADER_FONT)
add_text(s, "4 stages · TypeScript · axios", Inches(0.55), R1Y + Inches(0.5),
         rr_w, Inches(0.35),
         size=10, color=ICE, align=PP_ALIGN.CENTER, italic=True)
add_text(s, "Onboarding  ·  Elicitation  ·  Recommendations  ·  Refinement",
         Inches(0.55), R1Y + Inches(0.82),
         rr_w, Inches(0.3),
         size=9.5, color=ICE_DEEP, align=PP_ALIGN.CENTER)

# Backend (coral because it's where deterministic logic lives)
add_rect(s, Inches(4.7), R1Y, rr_w, R1H, CORAL)
add_text(s, "FastAPI Backend", Inches(4.7), R1Y + Inches(0.12),
         rr_w, Inches(0.4),
         bold=True, size=13, color=WHITE, align=PP_ALIGN.CENTER, font=HEADER_FONT)
add_text(s, "/start · /answer · /recommend · /refine",
         Inches(4.7), R1Y + Inches(0.5),
         rr_w, Inches(0.35),
         size=10, color=WHITE, align=PP_ALIGN.CENTER, italic=True)
add_text(s, "Orchestrates Claude + Rule-Based Engine",
         Inches(4.7), R1Y + Inches(0.82),
         rr_w, Inches(0.3),
         size=9.5, color=WHITE, align=PP_ALIGN.CENTER)

# Claude
add_rect(s, Inches(8.85), R1Y, rr_w, R1H, NAVY)
add_text(s, "Claude  (Opus 4.6)", Inches(8.85), R1Y + Inches(0.12),
         rr_w, Inches(0.4),
         bold=True, size=13, color=WHITE, align=PP_ALIGN.CENTER, font=HEADER_FONT)
add_text(s, "4 call sites · language only",
         Inches(8.85), R1Y + Inches(0.5),
         rr_w, Inches(0.35),
         size=10, color=ICE, align=PP_ALIGN.CENTER, italic=True)
add_text(s, "Parse · Clarify · Explain · Lifecycle",
         Inches(8.85), R1Y + Inches(0.82),
         rr_w, Inches(0.3),
         size=9.5, color=ICE_DEEP, align=PP_ALIGN.CENTER)

# arrows row 1
A_MID = R1Y + R1H / 2
for lx, rx in [(Inches(4.45), Inches(4.7)), (Inches(8.6), Inches(8.85))]:
    add_rect(s, lx, A_MID - Pt(1), rx - lx, Pt(2), NAVY)

# Row 2: engine, DB, ETL
R2Y = Inches(5.25); R2H = Inches(1.4)
rb_w = Inches(3.9); rb_gap = Inches(0.25)

add_rect(s, Inches(0.55), R2Y, rb_w, R2H, WHITE, line=True, line_color=CORAL)
add_text(s, "Recommendation Engine", Inches(0.55), R2Y + Inches(0.12),
         rb_w, Inches(0.4),
         bold=True, size=13, color=NAVY, align=PP_ALIGN.CENTER, font=HEADER_FONT)
add_text(s, "Hard constraints + two-tier scoring",
         Inches(0.55), R2Y + Inches(0.5),
         rb_w, Inches(0.35),
         size=10, color=DARK_TEXT, align=PP_ALIGN.CENTER, italic=True)
add_text(s, "Deterministic — no AI in ranking",
         Inches(0.55), R2Y + Inches(0.82),
         rb_w, Inches(0.35),
         size=10, color=CORAL_D, align=PP_ALIGN.CENTER, bold=True)

add_rect(s, Inches(4.7), R2Y, rb_w, R2H, WHITE, line=True, line_color=ICE_DEEP)
add_text(s, "Product Database", Inches(4.7), R2Y + Inches(0.12),
         rb_w, Inches(0.4),
         bold=True, size=13, color=NAVY, align=PP_ALIGN.CENTER, font=HEADER_FONT)
add_text(s, "products_clean.json  ·  100 products  ·  3 categories",
         Inches(4.7), R2Y + Inches(0.5),
         rb_w, Inches(0.35),
         size=10, color=DARK_TEXT, align=PP_ALIGN.CENTER, italic=True)
add_text(s, "Smart Display · Water Bottle · Kitchen Organizer",
         Inches(4.7), R2Y + Inches(0.82),
         rb_w, Inches(0.35),
         size=10, color=MUTED_D, align=PP_ALIGN.CENTER)

add_rect(s, Inches(8.85), R2Y, rb_w, R2H, WHITE, line=True, line_color=ICE_DEEP)
add_text(s, "ETL Pipeline", Inches(8.85), R2Y + Inches(0.12),
         rb_w, Inches(0.4),
         bold=True, size=13, color=NAVY, align=PP_ALIGN.CENTER, font=HEADER_FONT)
add_text(s, "Playwright  ·  Amazon + Target fallback",
         Inches(8.85), R2Y + Inches(0.5),
         rb_w, Inches(0.35),
         size=10, color=DARK_TEXT, align=PP_ALIGN.CENTER, italic=True)
add_text(s, "Normalize · Dedup · Offline batch feed",
         Inches(8.85), R2Y + Inches(0.82),
         rb_w, Inches(0.35),
         size=10, color=MUTED_D, align=PP_ALIGN.CENTER)

# vertical connectors (backend ↓ engine; engine ↔ db ← etl)
CX = Inches(4.7) + rr_w / 2
add_rect(s, CX - Pt(1), R1Y + R1H, Pt(2), R2Y - (R1Y + R1H), CORAL)

# engine ↔ db arrow (small)
eng_right = Inches(0.55) + rb_w
db_left = Inches(4.7)
A2 = R2Y + R2H / 2
add_rect(s, eng_right, A2 - Pt(1), db_left - eng_right, Pt(2), NAVY)

# db ← etl arrow
db_right = Inches(4.7) + rb_w
etl_left = Inches(8.85)
add_rect(s, db_right, A2 - Pt(1), etl_left - db_right, Pt(2), NAVY)

slide_num(s, 6, total=TOTAL, dark=True)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — Recommendation Algorithm  (DARK)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, NAVY)
add_rect(s, 0, 0, W, Inches(0.06), CORAL)

section_label(s, "06  ·  Recommendation Algorithm", ICE)
slide_title(s, "Deterministic Two-Tier Weighted Scoring", WHITE, 28)

# ── Left: algorithm flow ──────────────────────────────────────────────────────
SX = Inches(0.5); SW = Inches(5.9)
flow_y0 = Inches(1.8)
step_h = Inches(1.05); step_gap = Inches(0.15)
alg_steps = [
    ("①", "Hard Constraint Filter",
     "Budget & delivery deadline — non-negotiable.\nEliminated before scoring."),
    ("②", "Build Feasible Set",
     "Only products satisfying all hard constraints proceed.\nTypically ~100 → 10–20 candidates."),
    ("③", "Two-Tier Weighted Scoring",
     "General: rating · price · delivery (dynamic weights)\nFeature: category-specific attributes"),
    ("④", "Ranked Output",
     "Combined = α · General + (1 − α) · Feature,   α = 0.6\nTop N returned with all components preserved."),
]
for i, (num, title, desc) in enumerate(alg_steps):
    sy = flow_y0 + i * (step_h + step_gap)
    add_rect(s, SX, sy, SW, step_h, MID_BLUE)
    add_rect(s, SX, sy, Inches(0.7), step_h, CORAL)
    add_text(s, num, SX, sy + Inches(0.25),
             Inches(0.7), Inches(0.5),
             bold=True, size=24, color=WHITE,
             align=PP_ALIGN.CENTER, font=HEADER_FONT)
    add_text(s, title, SX + Inches(0.85), sy + Inches(0.1),
             SW - Inches(1.0), Inches(0.35),
             bold=True, size=13, color=WHITE, font=HEADER_FONT)
    add_text(s, desc, SX + Inches(0.85), sy + Inches(0.45),
             SW - Inches(1.0), Inches(0.6),
             size=10, color=ICE)

# ── Right: worked example ─────────────────────────────────────────────────────
EX = Inches(6.6); EW = Inches(6.3)

add_rect(s, EX, Inches(1.8), EW, Inches(0.55), CORAL)
add_text(s, "Worked Example — smart display, flexible budget, no rush",
         EX + Inches(0.15), Inches(1.87),
         EW - Inches(0.25), Inches(0.4),
         bold=True, size=11, color=WHITE, font=HEADER_FONT)

# Weights panel
add_rect(s, EX, Inches(2.4), EW, Inches(1.3), NAVY_DEEP,
         line=True, line_color=MID_BLUE)
add_text(s, "GENERAL  (dynamic, from user priorities)",
         EX + Inches(0.15), Inches(2.48),
         EW - Inches(0.3), Inches(0.25),
         bold=True, size=9, color=CORAL)
gen_chips = [("Rating", "50%"), ("Price", "30%"), ("Delivery", "20%")]
gw = Inches(2.0); ggap = Inches(0.05)
for i, (lbl, pct) in enumerate(gen_chips):
    cx = EX + Inches(0.15) + i * (gw + ggap)
    add_rect(s, cx, Inches(2.73), gw, Inches(0.35), MID_BLUE)
    add_text(s, f"{lbl}  {pct}", cx, Inches(2.77),
             gw, Inches(0.3),
             bold=True, size=10, color=WHITE, align=PP_ALIGN.CENTER)

add_text(s, "FEATURE  (category-specific — smart displays)",
         EX + Inches(0.15), Inches(3.14),
         EW - Inches(0.3), Inches(0.25),
         bold=True, size=9, color=CORAL)
feat_chips = [("Voice", "40%"), ("Screen", "30%"), ("Smart Home", "20%"), ("Brand", "10%")]
fw = Inches(1.48); fgap = Inches(0.06)
for i, (lbl, pct) in enumerate(feat_chips):
    cx = EX + Inches(0.15) + i * (fw + fgap)
    add_rect(s, cx, Inches(3.39), fw, Inches(0.3), MID_BLUE)
    add_text(s, f"{lbl}  {pct}", cx, Inches(3.42),
             fw, Inches(0.26),
             bold=True, size=9.5, color=WHITE, align=PP_ALIGN.CENTER)

# Product rows
prods = [
    (GREEN_OK, "✓  PASS",       "Amazon Echo Show 8",        "$79 · 4.7★ · 2-day",
     "Gen 0.82 · Feat 0.88",  "Combined 0.84   →  #1"),
    (GREEN_OK, "✓  PASS",       "Google Nest Hub (2nd Gen)", "$65 · 4.5★ · 3-day",
     "Gen 0.80 · Feat 0.79",  "Combined 0.80   →  #2"),
    (RED_NO,   "✗  ELIMINATED", "Amazon Echo Show 15",       "$249 · 4.8★ · 2-day",
     "over $80 budget",       "filtered before scoring"),
]
prod_y0 = Inches(3.85); ph = Inches(0.78); pgap = Inches(0.07)
for i, (bcol, badge, name, attrs, score, combined) in enumerate(prods):
    py = prod_y0 + i * (ph + pgap)
    row_fill = MID_BLUE if i % 2 == 0 else NAVY_DEEP
    add_rect(s, EX, py, EW, ph, row_fill)
    add_rect(s, EX, py, Inches(1.2), ph, bcol)
    add_text(s, badge, EX, py + Inches(0.25),
             Inches(1.2), Inches(0.35),
             bold=True, size=10, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, name, EX + Inches(1.3), py + Inches(0.06),
             Inches(3.0), Inches(0.3),
             bold=True, size=11, color=WHITE, font=HEADER_FONT)
    add_text(s, attrs, EX + Inches(1.3), py + Inches(0.38),
             Inches(3.0), Inches(0.3),
             size=9.5, color=ICE_DEEP)
    add_text(s, score, EX + Inches(4.3), py + Inches(0.06),
             Inches(1.95), Inches(0.3),
             size=9.5, color=ICE, align=PP_ALIGN.RIGHT)
    add_text(s, combined, EX + Inches(4.3), py + Inches(0.38),
             Inches(1.95), Inches(0.3),
             bold=True, size=10, color=CORAL, align=PP_ALIGN.RIGHT)

# Anchor footer
add_rect(s, Inches(0.5), Inches(6.9), Inches(12.4), Inches(0.42), CORAL)
add_text(s,
         "When the system decides what to show the user, AI steps aside.",
         Inches(0.5), Inches(6.95), Inches(12.4), Inches(0.35),
         bold=True, size=12, color=WHITE, align=PP_ALIGN.CENTER, font=HEADER_FONT)

slide_num(s, 7, total=TOTAL, dark=False)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — Data Pipeline  (LIGHT)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, LIGHT_BG)
top_accent(s, NAVY)
corner_motif(s, CORAL)

section_label(s, "07  ·  Data Pipeline", NAVY)
slide_title(s, "Playwright ETL  ·  Normalization  ·  Schema", NAVY, 28)

# Stage chain across the top
stages = [
    ("1", "Scrape",    "Amazon  →  Target",  "Primary + fallback"),
    ("2", "Normalize", "Prices · ratings",   "Delivery  →  days"),
    ("3", "Dedup",     "URL exact match",    "+ fuzzy title prefix"),
    ("4", "Validate",  "10-field schema",    "TypedDict contract"),
    ("5", "Emit",      "products_clean.json","100 products · 3 cats"),
]
stx0 = Inches(0.5); stw = Inches(2.42); stgap = Inches(0.1); sty = Inches(1.7)
for i, (num, title, line1, line2) in enumerate(stages):
    x = stx0 + i * (stw + stgap)
    add_rect(s, x, sty, stw, Inches(1.5), WHITE, line=True, line_color=ICE_DEEP)
    add_rect(s, x, sty, stw, Inches(0.45), NAVY)
    icon_circle(s, x + Inches(0.1), sty + Inches(0.05),
                Inches(0.35), CORAL, num, WHITE, 12)
    add_text(s, title, x + Inches(0.5), sty + Inches(0.08),
             stw - Inches(0.55), Inches(0.35),
             bold=True, size=13, color=WHITE, font=HEADER_FONT)
    add_text(s, line1, x + Inches(0.15), sty + Inches(0.6),
             stw - Inches(0.3), Inches(0.3),
             bold=True, size=11, color=NAVY)
    add_text(s, line2, x + Inches(0.15), sty + Inches(0.95),
             stw - Inches(0.3), Inches(0.3),
             size=10, color=MUTED_D, italic=True)
    if i < len(stages) - 1:
        add_text(s, "→", x + stw - Inches(0.05), sty + Inches(0.55),
                 stgap + Inches(0.05), Inches(0.4),
                 bold=True, size=16, color=CORAL)

# Normalization examples block (left) + Schema block (right)
NY = Inches(3.5)
add_rect(s, Inches(0.5), NY, Inches(6.2), Inches(3.3), WHITE,
         line=True, line_color=ICE_DEEP)
add_rect(s, Inches(0.5), NY, Inches(6.2), Inches(0.5), NAVY)
add_text(s, "Normalization Examples",
         Inches(0.65), NY + Inches(0.1), Inches(6.0), Inches(0.35),
         bold=True, size=14, color=WHITE, font=HEADER_FONT)
norm_rows = [
    ('"Arrives Mar 14"',       "→",   "5  (days from today)"),
    ('"Get it in 2–3 days"',   "→",   "3  (upper bound)"),
    ('"Ships within a week"',  "→",   "7"),
    ('"1K reviews"',           "→",   "1000"),
    ('"$79.99"',               "→",   "79.99"),
]
for i, (raw, arr, clean) in enumerate(norm_rows):
    y = NY + Inches(0.7) + i * Inches(0.48)
    add_text(s, raw, Inches(0.7), y,
             Inches(2.8), Inches(0.35),
             size=11, color=DARK_TEXT, font="Consolas")
    add_text(s, arr, Inches(3.4), y,
             Inches(0.4), Inches(0.35),
             bold=True, size=12, color=CORAL, align=PP_ALIGN.CENTER)
    add_text(s, clean, Inches(3.9), y,
             Inches(2.7), Inches(0.35),
             bold=True, size=11, color=NAVY, font="Consolas")

# Schema block
add_rect(s, Inches(6.85), NY, Inches(6.05), Inches(3.3), NAVY)
add_text(s, "ScrapedProduct  —  10-field TypedDict",
         Inches(7.0), NY + Inches(0.15), Inches(5.8), Inches(0.35),
         bold=True, size=13, color=WHITE, font=HEADER_FONT)
add_text(s, "flat schema · boring · easy to reason about",
         Inches(7.0), NY + Inches(0.5), Inches(5.8), Inches(0.3),
         size=10, color=CORAL, italic=True)

fields_l = ["title", "url", "image_url", "price", "rating"]
fields_r = ["review_count", "delivery_days", "source", "category", "fetched_at"]
for i, f in enumerate(fields_l):
    add_text(s, f"·  {f}", Inches(7.0), NY + Inches(0.95) + i * Inches(0.4),
             Inches(2.7), Inches(0.35),
             size=11, color=ICE, font="Consolas")
for i, f in enumerate(fields_r):
    add_text(s, f"·  {f}", Inches(9.9), NY + Inches(0.95) + i * Inches(0.4),
             Inches(2.9), Inches(0.35),
             size=11, color=ICE, font="Consolas")

# Stats bar
add_rect(s, Inches(0.5), Inches(6.95), Inches(12.4), Inches(0.4), CORAL)
add_text(s,
         "100 products  ·  3 categories  ·  2 active sources  ·  two-phase dedup",
         Inches(0.5), Inches(7.0), Inches(12.4), Inches(0.3),
         bold=True, size=11, color=WHITE, align=PP_ALIGN.CENTER, font=HEADER_FONT)

slide_num(s, 8, total=TOTAL, dark=True)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — Results & Demo  (DARK)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, NAVY)
add_rect(s, 0, 0, W, Inches(0.06), CORAL)

section_label(s, "08  ·  Results & Demo", ICE)
slide_title(s, "Capability Validation & Scenario Walkthrough", WHITE, 26)

# Stat callouts — big numbers
stats = [
    ("6 / 6", "capability gaps\naddressed",        CORAL),
    ("4",     "Claude call sites\n(none in ranking)", MID_BLUE),
    ("0",     "LLM inference in\nthe ranking step",    CORAL),
    ("100",   "products\nacross 3 categories",      MID_BLUE),
]
sx0 = Inches(0.5); sw = Inches(3.03); sgap = Inches(0.12); sy = Inches(1.75)
for i, (big, small, fill) in enumerate(stats):
    x = sx0 + i * (sw + sgap)
    add_rect(s, x, sy, sw, Inches(1.9), fill)
    add_text(s, big, x, sy + Inches(0.15),
             sw, Inches(1.05),
             bold=True, size=56, color=WHITE,
             align=PP_ALIGN.CENTER, font=HEADER_FONT)
    add_text(s, small, x, sy + Inches(1.2),
             sw, Inches(0.6),
             size=11, color=ICE, align=PP_ALIGN.CENTER)

# Demo walkthrough (left) + Validation findings (right)
DY = Inches(3.85); DH = Inches(2.95)

add_rect(s, Inches(0.5), DY, Inches(6.2), DH, MID_BLUE)
add_text(s, "Demo  —  Kitchen Assistant Scenario",
         Inches(0.65), DY + Inches(0.1), Inches(5.9), Inches(0.4),
         bold=True, size=14, color=WHITE, font=HEADER_FONT)
demo_steps = [
    ("①  Onboarding",
     "'I want something for cooking' → smart display"),
    ("②  Elicitation",
     "5 guided Qs: budget, screen, delivery, household, voice"),
    ("③  Recommendations",
     "Ranked list + trade-off explanation per product"),
    ("④  Refinement",
     "Deprioritize screen → re-rank + lifecycle ideas"),
]
for i, (step, desc) in enumerate(demo_steps):
    y = DY + Inches(0.6) + i * Inches(0.56)
    add_text(s, step, Inches(0.75), y,
             Inches(2.3), Inches(0.35),
             bold=True, size=11, color=CORAL, font=HEADER_FONT)
    add_text(s, desc, Inches(3.1), y,
             Inches(3.5), Inches(0.35),
             size=10.5, color=WHITE)

add_rect(s, Inches(6.85), DY, Inches(6.05), DH, NAVY_DEEP,
         line=True, line_color=CORAL)
add_text(s, "Validation Findings",
         Inches(7.0), DY + Inches(0.1), Inches(5.75), Inches(0.4),
         bold=True, size=14, color=WHITE, font=HEADER_FONT)
findings = [
    ("Information completeness",
     "price, rating, delivery, promos — all in one view"),
    ("Interaction efficiency",
     "4-stage flow · zero external page navigation"),
    ("Decision transparency",
     "every rec carries an explanation tied to priorities"),
    ("Reproducibility",
     "identical inputs → identical ranking"),
]
for i, (title, body) in enumerate(findings):
    y = DY + Inches(0.6) + i * Inches(0.56)
    add_text(s, "✓  " + title, Inches(7.0), y,
             Inches(5.75), Inches(0.35),
             bold=True, size=11, color=GREEN_OK)
    add_text(s, body, Inches(7.3), y + Inches(0.3),
             Inches(5.45), Inches(0.3),
             size=10, color=ICE)

# Honest caveat
add_rect(s, Inches(0.5), Inches(6.95), Inches(12.4), Inches(0.4), NAVY_DEEP)
add_text(s,
         "Heuristic self-assessment against the six capability gaps  ·  formal user study is future work",
         Inches(0.5), Inches(7.0), Inches(12.4), Inches(0.3),
         size=10, color=ICE_DEEP, italic=True, align=PP_ALIGN.CENTER)

slide_num(s, 9, total=TOTAL, dark=False)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — Limitations · Conclusions · Future Work  (LIGHT)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, LIGHT_BG)
top_accent(s, NAVY)
corner_motif(s, CORAL)

section_label(s, "09  ·  Honest Assessment", NAVY)
slide_title(s, "What This Proves  ·  What It Doesn't  ·  What's Next", NAVY, 26)

col_w = Inches(4.0); col_gap = Inches(0.25)
col_x = [
    Inches(0.5),
    Inches(0.5) + col_w + col_gap,
    Inches(0.5) + 2 * (col_w + col_gap),
]
col_y = Inches(1.75); col_h = Inches(5.2)
col_titles = ["Limitations", "Conclusions & Impact", "Future Work"]
col_fills  = [CORAL, NAVY, MID_BLUE]

for x, title, fill in zip(col_x, col_titles, col_fills):
    # White card
    add_rect(s, x, col_y, col_w, col_h, WHITE, line=True, line_color=ICE_DEEP)
    # Colored header band
    add_rect(s, x, col_y, col_w, Inches(0.55), fill)
    add_text(s, title, x + Inches(0.2), col_y + Inches(0.12),
             col_w - Inches(0.3), Inches(0.35),
             bold=True, size=15, color=WHITE, font=HEADER_FONT)

lims = [
    ("Small dataset",       "100 products · 3 categories only"),
    ("No user study",       "heuristic evaluation only"),
    ("Static data",         "prices & delivery change dynamically"),
    ("Rule-based weights",  "inferred, not learned"),
]
cons = [
    ("Decision support feasible",  "end-to-end with Claude Opus 4.6"),
    ("Structured elicitation",     "designed to address cognitive load"),
    ("Explainable trade-offs",     "transparent, reproducible rankings"),
    ("ETL validates the approach", "Playwright scrape · normalize · dedup"),
    ("Lifecycle value",            "extends past the purchase itself"),
]
fut = [
    ("Formal user study",  "SUS + task completion time"),
    ("Live retailer API",  "real-time pricing"),
    ("Learned ranking",    "from interaction data"),
    ("More categories",    "beyond the current three"),
    ("Mobile-first UI",    "redesign for small screens"),
]

def render_col(x, items, icon, icon_color):
    for i, (title, body) in enumerate(items):
        y = col_y + Inches(0.75) + i * Inches(0.85)
        icon_circle(s, x + Inches(0.2), y, Inches(0.35), icon_color, icon, WHITE, 12)
        add_text(s, title, x + Inches(0.65), y - Inches(0.02),
                 col_w - Inches(0.8), Inches(0.35),
                 bold=True, size=12, color=NAVY, font=HEADER_FONT)
        add_text(s, body, x + Inches(0.65), y + Inches(0.3),
                 col_w - Inches(0.8), Inches(0.5),
                 size=10, color=DARK_TEXT)

render_col(col_x[0], lims, "!", CORAL)
render_col(col_x[1], cons, "✓", NAVY)
render_col(col_x[2], fut,  "→", MID_BLUE)

slide_num(s, 10, total=TOTAL, dark=True)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — Thank You / Q&A  (DARK)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, NAVY)
add_rect(s, 0, Inches(6.7), W, Inches(0.1), CORAL)

add_text(s, "Thank You",
         Inches(1.0), Inches(1.4), Inches(11.3), Inches(1.4),
         bold=True, size=72, color=WHITE, align=PP_ALIGN.CENTER, font=HEADER_FONT)
add_text(s, "Questions  &  Discussion",
         Inches(1.0), Inches(2.9), Inches(11.3), Inches(0.6),
         size=24, color=ICE, align=PP_ALIGN.CENTER, font=HEADER_FONT)

# Coral underline bar (not an accent divider — semantic boundary motif)
add_rect(s, Inches(5.2), Inches(3.7), Inches(2.93), Inches(0.05), CORAL)

# Info block in a card
IY = Inches(4.2); IH = Inches(2.2)
add_rect(s, Inches(2.0), IY, Inches(9.33), IH, NAVY_DEEP,
         line=True, line_color=MID_BLUE)

info_items = [
    ("Author",      "Chenghui Tan"),
    ("Institution", "California State University, East Bay  ·  CSUEB"),
    ("Project",     "A Decision-Oriented Conversational Shopping Assistant"),
    ("Stack",       "React · TypeScript · FastAPI · Python · Claude Opus 4.6 · Playwright"),
]
for i, (label, value) in enumerate(info_items):
    y = IY + Inches(0.2) + i * Inches(0.48)
    add_text(s, label, Inches(2.3), y, Inches(2.2), Inches(0.4),
             bold=True, size=12, color=CORAL, font=HEADER_FONT)
    add_text(s, value, Inches(4.6), y, Inches(6.5), Inches(0.4),
             size=13, color=WHITE)

slide_num(s, 11, total=TOTAL, dark=False)

# ── Save ──────────────────────────────────────────────────────────────────────
out = "/Users/sabrina/Projects/shopping-assistant-4/docs/capstone_presentation_v3.pptx"
prs.save(out)
print(f"Saved → {out}  ({len(prs.slides)} slides)")
