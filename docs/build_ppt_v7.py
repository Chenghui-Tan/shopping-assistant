"""
Capstone Presentation — 11 slides
A Decision-Oriented Conversational Shopping Assistant
Chenghui Tan — CSUEB
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

# ── Palette ───────────────────────────────────────────────────────────────────
NAVY      = RGBColor(0x1E, 0x27, 0x61)
ICE       = RGBColor(0xCA, 0xDC, 0xFC)
WHITE     = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_BG  = RGBColor(0xF4, 0xF6, 0xFD)
MID_BLUE  = RGBColor(0x3A, 0x4F, 0x9B)
DARK_TEXT = RGBColor(0x1A, 0x1A, 0x2E)
MUTED     = RGBColor(0x6B, 0x7A, 0xB8)
GREEN_OK  = RGBColor(0x2E, 0xCC, 0x71)
RED_NO    = RGBColor(0xE7, 0x4C, 0x3C)
CHIP_RED  = RGBColor(0x8B, 0x1A, 0x1A)
TEAL      = RGBColor(0x02, 0x80, 0x90)
PURPLE    = RGBColor(0x5B, 0x2D, 0x8E)
ORANGE    = RGBColor(0xC0, 0x5A, 0x10)

W = Inches(13.33)
H = Inches(7.5)

# ── Helpers ───────────────────────────────────────────────────────────────────
def add_rect(slide, l, t, w, h, fill):
    s = slide.shapes.add_shape(1, l, t, w, h)
    s.line.fill.background()
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    return s

def add_text(slide, text, l, t, w, h,
             bold=False, size=18, color=WHITE,
             align=PP_ALIGN.LEFT, wrap=True, italic=False):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    run.font.bold = bold
    run.font.italic = italic
    run.font.size = Pt(size)
    run.font.color.rgb = color
    return tb

def bg(slide, color):
    add_rect(slide, 0, 0, W, H, color)

def top_bar(slide, color=ICE):
    add_rect(slide, 0, 0, W, Inches(0.08), color)

def bot_bar(slide, color=ICE):
    add_rect(slide, 0, H - Inches(0.08), W, Inches(0.08), color)

def section_label(slide, text, color=ICE):
    add_text(slide, text.upper(),
             Inches(0.5), Inches(0.22), Inches(12), Inches(0.35),
             bold=True, size=9, color=color)

def slide_title(slide, text, color=WHITE, size=34):
    add_text(slide, text,
             Inches(0.55), Inches(0.6), Inches(12.2), Inches(1.0),
             bold=True, size=size, color=color)

def divider(slide, y, color=ICE, w=12.3):
    r = slide.shapes.add_shape(1,
        Inches(0.5), Inches(y), Inches(w), Pt(1.5))
    r.fill.solid(); r.fill.fore_color.rgb = color
    r.line.fill.background()

def slide_num(slide, n, total=12, dark=True):
    c = MUTED if dark else RGBColor(0x9A, 0xA8, 0xCC)
    add_text(slide, f"{n} / {total}",
             Inches(12.1), H - Inches(0.45), Inches(1.1), Inches(0.35),
             size=9, color=c, align=PP_ALIGN.RIGHT)


def add_notes(slide, text):
    """Attach speaker notes so dense detail can live off-slide."""
    notes_tf = slide.notes_slide.notes_text_frame
    notes_tf.clear()
    notes_tf.text = text

# ── Presentation ──────────────────────────────────────────────────────────────
prs = Presentation()
prs.slide_width  = W
prs.slide_height = H
BL = prs.slide_layouts[6]

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 1 — Title  (DARK)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, NAVY); top_bar(s, ICE); bot_bar(s, ICE)

add_text(s, "APPLIED RESEARCH PROJECT  ·  CAPSTONE PRESENTATION",
         Inches(0.55), Inches(1.5), Inches(12), Inches(0.4),
         bold=True, size=9, color=ICE)
add_text(s, "A Decision-Oriented Conversational\nShopping Assistant",
         Inches(0.55), Inches(1.95), Inches(12.2), Inches(2.2),
         bold=True, size=44, color=WHITE)
add_text(s, "Preference Elicitation · Explainable Recommendations · Lifecycle Support",
         Inches(0.55), Inches(4.05), Inches(12), Inches(0.55),
         size=16, color=ICE)
r = s.shapes.add_shape(1, Inches(0.5), Inches(4.75),
                        Inches(11.8), Pt(1.5))
r.fill.solid(); r.fill.fore_color.rgb = ICE; r.line.fill.background()
add_text(s, "Chenghui Tan",
         Inches(0.55), Inches(4.9), Inches(6), Inches(0.45),
         bold=True, size=15, color=WHITE)
add_text(s, "California State University, East Bay  ·  April 2026",
         Inches(0.55), Inches(5.35), Inches(8), Inches(0.4),
         size=12, color=MUTED)
slide_num(s, 1)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 2 — Introduction & Business Problem  (LIGHT)
# Fix: removed solution-preview right side; replaced with consequence framing
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, LIGHT_BG); top_bar(s, NAVY); bot_bar(s, NAVY)

section_label(s, "01  ·  Introduction & Business Problem", NAVY)
slide_title(s, "Information Retrieval  ≠  Decision Support", NAVY, 32)
divider(s, 1.62, NAVY)

# Left — 4 pain points
problems = [
    ("🧠", "Cognitive Overload",
     "Users must mentally juggle all constraints and trade-offs themselves"),
    ("❓", "Vague, Evolving Needs",
     "Users rarely know exactly what they want when they start"),
    ("🔄", "Preferences Get Overwritten",
     "Add a new constraint — your earlier choices are erased"),
    ("📦", "Missing Critical Info",
     "Delivery time, promos, and availability hidden or absent"),
]
for i, (icon, title, desc) in enumerate(problems):
    y = Inches(1.82) + i * Inches(1.28)
    add_rect(s, Inches(0.45), y, Inches(5.9), Inches(1.18), MID_BLUE)
    add_text(s, icon, Inches(0.55), y + Inches(0.22),
             Inches(0.55), Inches(0.6), size=20, color=WHITE)
    add_text(s, title, Inches(1.15), y + Inches(0.1),
             Inches(5.0), Inches(0.42), bold=True, size=13, color=ICE)
    add_text(s, desc, Inches(1.15), y + Inches(0.52),
             Inches(5.0), Inches(0.55), size=11, color=WHITE)

# Right — consequence / reframe
add_rect(s, Inches(6.6), Inches(1.82), Inches(6.25), Inches(5.12), NAVY)
add_text(s, "The Decision Burden Falls on the User",
         Inches(6.78), Inches(1.95), Inches(5.9), Inches(0.55),
         bold=True, size=14, color=ICE)

add_text(s,
         "Existing tools assume shopping is a search problem.\n"
         "In reality, users face a decision problem —\n"
         "and no platform is built to help them solve it.",
         Inches(6.78), Inches(2.62), Inches(5.9), Inches(1.1),
         size=12, color=WHITE, italic=True)

divider(s, 3.9, ICE, 5.7)

consequences = [
    "Decision fatigue increases with more options",
    "Users guess, settle, or abandon purchases",
    "Post-purchase regret when trade-offs aren't clear",
    "Trust erodes when recommendations have no rationale",
]
for i, c in enumerate(consequences):
    add_text(s, f"·  {c}",
             Inches(6.78), Inches(4.05) + i * Inches(0.65),
             Inches(5.9), Inches(0.6), size=11, color=WHITE)

add_rect(s, Inches(6.6), Inches(6.5), Inches(6.25), Inches(0.42), MID_BLUE)
add_text(s, "→  We built a system that addresses the decision — not just the search.",
         Inches(6.75), Inches(6.53), Inches(6.0), Inches(0.38),
         bold=True, size=11, color=ICE)

slide_num(s, 2, dark=False)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 3 — The Market & The Gaps  (DARK)
# Fix: "Shared Gaps" → "Key Gaps Across the Landscape"
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, NAVY); top_bar(s, ICE); bot_bar(s, ICE)

section_label(s, "02  ·  The Market & The Gaps")
slide_title(s, "Existing Platforms — Where They Fall Short")
divider(s, 1.62)

platforms = [
    ("Google\nShopping",  "Search & filter",      TEAL),
    ("Amazon\nRufus",     "AI chat in Amazon",    MID_BLUE),
    ("ChatGPT\nShopping", "Natural language AI",  PURPLE),
    ("Perplexity",        "AI answer engine",     ORANGE),
]
plat_w = Inches(2.9); plat_h = Inches(1.2); plat_gap = Inches(0.28)
plat_x0 = Inches(0.55)

for i, (name, desc, color) in enumerate(platforms):
    x = plat_x0 + i * (plat_w + plat_gap)
    add_rect(s, x, Inches(1.78), plat_w, plat_h, color)
    add_text(s, name, x + Inches(0.12), Inches(1.82),
             plat_w - Inches(0.22), Inches(0.65),
             bold=True, size=16, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, desc, x + Inches(0.12), Inches(2.42),
             plat_w - Inches(0.22), Inches(0.45),
             size=10, color=ICE, align=PP_ALIGN.CENTER)

# Fixed label — no longer claims all gaps are "shared"
add_text(s, "KEY GAPS ACROSS THE LANDSCAPE",
         Inches(0.55), Inches(3.1), Inches(12), Inches(0.35),
         bold=True, size=10, color=ICE)

gaps = [
    "✗  Overwrites preferences mid-conversation",
    "✗  Assumes you already know what you want",
    "✗  Missing delivery, promos & availability",
    "✗  Text heavy — low information density",
    "✗  No preference continuity across turns",
    "✗  Multiple steps to reach product page",
    "✗  Separates reasoning from shopping flow",
    "✗  Opaque ranking — no explanation why",
    "✗  Not built for first-time / cold-start users",
]

chip_w = Inches(3.95); chip_h = Inches(0.52)
chip_gap_x = Inches(0.28); chip_gap_y = Inches(0.12)
chip_x0 = Inches(0.55); chip_y0 = Inches(3.52)

for i, gap_text in enumerate(gaps):
    row = i // 3; col = i % 3
    x = chip_x0 + col * (chip_w + chip_gap_x)
    y = chip_y0 + row * (chip_h + chip_gap_y)
    add_rect(s, x, y, chip_w, chip_h, CHIP_RED)
    add_text(s, gap_text, x + Inches(0.1), y + Inches(0.08),
             chip_w - Inches(0.18), chip_h - Inches(0.1),
             size=11, color=WHITE)

# Insight bar — the common thread that ties every gap together
add_rect(s, Inches(0.55), Inches(5.95), Inches(12.25), Inches(0.58), MID_BLUE)
add_text(s,
         "→  The common thread: no platform treats shopping as a decision problem.",
         Inches(0.55), Inches(5.95), Inches(12.25), Inches(0.58),
         bold=True, size=13, color=ICE, align=PP_ALIGN.CENTER)

# Supporting stat strip — three framings of the same core failure
stat_items = [
    ("Search-first tools",   "→  retrieve results,  not decisions"),
    ("AI chatbots",          "→  converse,  but don't structure trade-offs"),
    ("All surveyed platforms", "→  no preference continuity across turns"),
]
stat_x0 = Inches(0.55); stat_w = Inches(3.75); stat_gap = Inches(0.1)
for i, (left, right) in enumerate(stat_items):
    x = stat_x0 + i * (stat_w + stat_gap)
    add_rect(s, x, Inches(6.72), stat_w, Inches(0.5), RGBColor(0x2A, 0x35, 0x75))
    add_text(s, left, x + Inches(0.12), Inches(6.75),
             stat_w - Inches(0.22), Inches(0.2),
             bold=True, size=9, color=ICE)
    add_text(s, right, x + Inches(0.12), Inches(6.95),
             stat_w - Inches(0.22), Inches(0.22),
             size=9, color=WHITE)

slide_num(s, 3)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 4 — Competitive Analysis  (LIGHT)
# Fix: moved before Our Product; renamed from "Related Work" to "Competitive Analysis"
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, LIGHT_BG); top_bar(s, NAVY); bot_bar(s, NAVY)

section_label(s, "03  ·  Competitive Analysis", NAVY)
slide_title(s, "Capability Comparison Across Platforms", NAVY, 32)
divider(s, 1.62, NAVY)

col_labels = ["Capability", "Google\nShopping", "Amazon\nRufus",
              "ChatGPT\nShopping", "Perplexity", "Our\nSystem"]
col_w = [Inches(3.2), Inches(1.6), Inches(1.6), Inches(1.6), Inches(1.6), Inches(1.8)]
x_starts = [Inches(0.45)]
for cw in col_w[:-1]:
    x_starts.append(x_starts[-1] + cw)

row_h = Inches(0.58); header_y = Inches(1.74)

for i, (label, x, cw) in enumerate(zip(col_labels, x_starts, col_w)):
    fill = NAVY if i == 0 else MID_BLUE
    add_rect(s, x, header_y, cw - Inches(0.03), row_h, fill)
    add_text(s, label, x + Inches(0.05), header_y + Inches(0.08),
             cw - Inches(0.1), row_h,
             bold=True, size=10, color=ICE if i > 0 else WHITE,
             align=PP_ALIGN.CENTER)

rows_data = [
    ("Preference Elicitation",        "✗",      "Partial", "Partial", "✗", "✓"),
    ("Decision Modeling",             "✗",      "✗",       "✗",       "✗", "✓"),
    ("Explainable Recommendations",   "✗",      "✗",       "Partial", "✓", "✓"),
    ("Delivery / Promo Info",         "Partial","✗",       "✗",       "✗", "✓"),
    ("Preference Continuity",         "✗",      "Partial", "Partial", "✗", "✓"),
    ("Side-by-Side Comparison",       "✗",      "✗",       "✗",       "✗", "✓"),
    ("Lifecycle Support",             "✗",      "✗",       "✗",       "✗", "✓"),
]

for r, (row_label, *vals) in enumerate(rows_data):
    y = header_y + row_h * (r + 1) + Inches(0.04)
    row_fill = LIGHT_BG if r % 2 == 0 else RGBColor(0xE2, 0xE8, 0xF8)
    add_rect(s, x_starts[0], y, col_w[0] - Inches(0.03),
             row_h - Inches(0.04), RGBColor(0xD6, 0xDE, 0xF7))
    add_text(s, row_label, x_starts[0] + Inches(0.1), y + Inches(0.15),
             col_w[0] - Inches(0.15), row_h, size=11, color=DARK_TEXT)
    for j, (val, x, cw) in enumerate(zip(vals, x_starts[1:], col_w[1:]), 1):
        add_rect(s, x, y, cw - Inches(0.03), row_h - Inches(0.04), row_fill)
        c = GREEN_OK if val == "✓" else RED_NO if val == "✗" else MUTED
        add_text(s, val, x, y + Inches(0.1), cw - Inches(0.03), row_h,
                 bold=(val in ("✓", "✗")), size=14, color=c,
                 align=PP_ALIGN.CENTER)

# Bridge — now logically positioned: comparison complete → here's our solution
add_rect(s, Inches(0.45), Inches(6.65), Inches(12.4), Inches(0.43), NAVY)
add_text(s,
         "→  In our self-evaluation against these platforms, our system addresses all seven gaps.  "
         "Here is how we built it.",
         Inches(0.65), Inches(6.69), Inches(12.0), Inches(0.36),
         bold=True, size=12, color=ICE)

slide_num(s, 4, dark=False)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 5 — Our Product  (DARK)
# Fix: moved after comparison; fixed abstract chip labels
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, NAVY); top_bar(s, ICE); bot_bar(s, ICE)

section_label(s, "04  ·  Our Product")
slide_title(s, "Your Personal AI Shopping Assistant")
divider(s, 1.62)

clusters = [
    ("🧠", "Understand You", TEAL,
     ["Frustration → Category",
      "Decision-Relevant Q&A"],
     "ecosystem · placement · privacy · size"),
    ("👤", "Remembers You", MID_BLUE,
     ["Preference Continuity",
      "Visible Diff on Refine"],
     "“leaks” → leak-proof  ·  “heavy” → lightweight"),
    ("✨", "Clear Decisions", PURPLE,
     ["3 Curated Picks",
      "Why-this-fits  ·  Compare"],
     "Best Fit · Budget Pick · Stretch Pick"),
]

card_w = Inches(3.8); card_h = Inches(4.5)
card_gap = Inches(0.45); card_x0 = Inches(0.6); card_y = Inches(1.82)

for i, (icon, title, color, chips_list, example) in enumerate(clusters):
    x = card_x0 + i * (card_w + card_gap)
    add_rect(s, x, card_y, card_w, card_h, color)
    add_rect(s, x + Inches(1.4), card_y + Inches(0.18),
             Inches(1.0), Inches(0.8), NAVY)
    add_text(s, icon,
             x + Inches(1.4), card_y + Inches(0.18),
             Inches(1.0), Inches(0.8),
             size=24, align=PP_ALIGN.CENTER)
    add_text(s, title,
             x + Inches(0.12), card_y + Inches(1.1),
             card_w - Inches(0.22), Inches(0.55),
             bold=True, size=16, color=WHITE, align=PP_ALIGN.CENTER)
    for j, chip_text in enumerate(chips_list):
        cy = card_y + Inches(1.72) + j * Inches(0.7)
        add_rect(s, x + Inches(0.25), cy,
                 card_w - Inches(0.5), Inches(0.55), NAVY)
        add_text(s, chip_text,
                 x + Inches(0.25), cy,
                 card_w - Inches(0.5), Inches(0.55),
                 bold=True, size=12, color=ICE, align=PP_ALIGN.CENTER)
    # Concrete example footer inside each card
    add_text(s, example,
             x + Inches(0.2), card_y + card_h - Inches(0.6),
             card_w - Inches(0.4), Inches(0.5),
             size=10, color=ICE, italic=True, align=PP_ALIGN.CENTER)

add_rect(s, Inches(0.6), Inches(6.48), Inches(12.15), Inches(0.58), ORANGE)
add_text(s, "🏠  Lifecycle Layer (prototype)  —  Realistic post-purchase support",
         Inches(0.6), Inches(6.48), Inches(12.15), Inches(0.58),
         bold=True, size=13, color=WHITE, align=PP_ALIGN.CENTER)

add_notes(s,
    "Talking points for this slide:\n"
    "1. UNDERSTAND YOU — the assistant lets the user start from a frustration "
    "('phone screen too small for cooking') instead of a category. Six chip "
    "questions per category — voice ecosystem, placement, screen size, privacy, "
    "etc. — are decision-relevant, not generic budget/urgency.\n"
    "2. REMEMBERS YOU — every refine turn captures a preference diff and "
    "renders it as a 'What changed' card. Implicit prefs are inferred from the "
    "free-text frustration ('leaks' -> leak-resistant, 'heavy' -> lightweight).\n"
    "3. CLEAR DECISIONS — the assistant returns 3 differentiated picks "
    "(Best Fit / Budget Pick / Stretch). Each pick carries a ✓/✗/? checklist "
    "mapping every chip the user picked to a match status. Compare view "
    "lays 2-3 finalists side-by-side with row-winners highlighted.\n"
    "4. LIFECYCLE LAYER — framed as a prototype concept that demonstrates "
    "the assistant continuing to add value after purchase (phone reminders, "
    "gym-bag checklist, replacement parts). Not a finished post-purchase "
    "platform.")

slide_num(s, 5)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 6 — Architecture Overview  (LIGHT)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, LIGHT_BG); top_bar(s, NAVY); bot_bar(s, NAVY)

section_label(s, "05A  ·  Conceptual Architecture", NAVY)
slide_title(s, "Five-Layer Decision Support Framework", NAVY, 32)
divider(s, 1.62, NAVY)

layers = [
    ("1", "Preference\nElicitation",
     "Transforms vague needs\ninto structured inputs\nvia conversational Q&A"),
    ("2", "Decision\nModeling",
     "Multi-criteria model:\nhard constraints +\nweighted soft preferences"),
    ("3", "Recommendation\n& Ranking",
     "Constraint-aware ranking\nof feasible products;\nno click-prediction bias"),
    ("4", "Explainability\n& Interaction",
     "Why this fits, what\nyou give up — trade-offs\nmade transparent"),
    ("5", "Lifecycle\nSupport",
     "Post-purchase value:\nmeal planning, scheduling,\ndecision reinforcement"),
]
box_w = Inches(2.2); box_h = Inches(3.8)
gap = Inches(0.28); sx = Inches(0.5)

for i, (num, title, desc) in enumerate(layers):
    x = sx + i * (box_w + gap)
    add_rect(s, x, Inches(1.75), box_w, box_h, MID_BLUE)
    add_rect(s, x + Inches(0.8), Inches(1.82), Inches(0.6), Inches(0.5), NAVY)
    add_text(s, num, x + Inches(0.8), Inches(1.82),
             Inches(0.6), Inches(0.5),
             bold=True, size=16, color=ICE, align=PP_ALIGN.CENTER)
    add_text(s, title, x + Inches(0.1), Inches(2.45),
             box_w - Inches(0.2), Inches(0.9),
             bold=True, size=13, color=ICE, align=PP_ALIGN.CENTER)
    add_text(s, desc, x + Inches(0.12), Inches(3.45),
             box_w - Inches(0.22), Inches(2.0),
             size=11, color=DARK_TEXT, align=PP_ALIGN.LEFT)
    if i < len(layers) - 1:
        add_text(s, "→", x + box_w + Inches(0.02), Inches(2.9),
                 gap, Inches(0.5), bold=True, size=18, color=NAVY,
                 align=PP_ALIGN.CENTER)

add_text(s,
         "End-to-end: vague need → structured decision → ranked products → explained trade-offs → lifecycle value",
         Inches(0.5), Inches(5.75), Inches(12.3), Inches(0.5),
         size=11, color=MUTED, align=PP_ALIGN.CENTER, italic=True)

slide_num(s, 6, dark=False)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 7 — Architecture: Tech & Interactions  (DARK)
# Redesigned: component interaction diagram with arrows
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, NAVY); top_bar(s, ICE); bot_bar(s, ICE)

section_label(s, "05B  ·  Runtime Architecture — Tech & Interactions")
slide_title(s, "Components & How They Communicate")
divider(s, 1.62)

# ── Row 1 boxes ───────────────────────────────────────────────────────────────
R1Y = Inches(1.88); R1H = Inches(2.0)

# React Frontend
add_rect(s, Inches(0.35), R1Y, Inches(2.8), R1H, TEAL)
add_text(s, "React Frontend",
         Inches(0.45), R1Y+Inches(0.09), Inches(2.6), Inches(0.42),
         bold=True, size=12, color=WHITE, align=PP_ALIGN.CENTER)
add_text(s, "Stage 1 — Need Discovery\nStage 2 — Clarification Q&A\nStage 3 — 3 Curated Picks\nStage 4 — Why This Fits\nStage 5 — Lifecycle",
         Inches(0.47), R1Y+Inches(0.58), Inches(2.56), Inches(1.3),
         size=10, color=WHITE)

# FastAPI Backend
add_rect(s, Inches(4.65), R1Y, Inches(3.7), R1H, MID_BLUE)
add_text(s, "FastAPI Backend",
         Inches(4.75), R1Y+Inches(0.09), Inches(3.5), Inches(0.42),
         bold=True, size=12, color=WHITE, align=PP_ALIGN.CENTER)
add_text(s, "/start  /answer  /recommend\n/refine  /save  /lifecycle",
         Inches(4.75), R1Y+Inches(0.58), Inches(3.5), Inches(0.5),
         size=11, color=ICE, align=PP_ALIGN.CENTER)
add_text(s, "Orchestrates all logic + deterministic\nfallbacks (regex refine, classifier)",
         Inches(4.75), R1Y+Inches(1.18), Inches(3.5), Inches(0.65),
         size=10, color=WHITE, align=PP_ALIGN.CENTER)

# Claude (language only — never ranking)
add_rect(s, Inches(9.65), R1Y, Inches(3.35), R1H, PURPLE)
add_text(s, "Claude Opus 4.6  (AI)",
         Inches(9.75), R1Y+Inches(0.09), Inches(3.15), Inches(0.42),
         bold=True, size=12, color=WHITE, align=PP_ALIGN.CENTER)
add_text(s, "Parse free-text input\nWrite personal copy\nParse refine intent\n(deterministic fallback per call)",
         Inches(9.77), R1Y+Inches(0.58), Inches(3.1), Inches(1.3),
         size=10, color=WHITE)

# ── Row 2 boxes ───────────────────────────────────────────────────────────────
R2Y = Inches(4.5); R2H = Inches(1.8)

# Recommendation Engine
add_rect(s, Inches(3.5), R2Y, Inches(2.8), R2H, ORANGE)
add_text(s, "Recommendation Engine",
         Inches(3.6), R2Y+Inches(0.09), Inches(2.6), Inches(0.42),
         bold=True, size=10, color=WHITE, align=PP_ALIGN.CENTER)
add_text(s, "Filter · score · rank\nCurated 3 picks\nTradeoff labels (factual)\nDeterministic — no AI",
         Inches(3.62), R2Y+Inches(0.58), Inches(2.56), Inches(1.1),
         size=9.5, color=WHITE)

# Product DB
add_rect(s, Inches(6.6), R2Y, Inches(2.8), R2H, TEAL)
add_text(s, "Product DB",
         Inches(6.7), R2Y+Inches(0.09), Inches(2.6), Inches(0.42),
         bold=True, size=11, color=WHITE, align=PP_ALIGN.CENTER)
add_text(s, "products_clean.json\n100 products · 3 categories\nSmart Display · Water Bottle\nKitchen Organizer",
         Inches(6.72), R2Y+Inches(0.58), Inches(2.56), Inches(1.1),
         size=9.5, color=WHITE)

# ETL Pipeline
add_rect(s, Inches(9.7), R2Y, Inches(3.0), R2H, RGBColor(0x2A,0x35,0x75))
add_text(s, "ETL Pipeline",
         Inches(9.8), R2Y+Inches(0.09), Inches(2.8), Inches(0.42),
         bold=True, size=11, color=ICE, align=PP_ALIGN.CENTER)
add_text(s, "Playwright scrapers\nAmazon · Target\nNormalize & deduplicate\nOffline batch feed",
         Inches(9.82), R2Y+Inches(0.58), Inches(2.76), Inches(1.1),
         size=9.5, color=WHITE)

# ── Arrows ────────────────────────────────────────────────────────────────────
A_MID = R1Y + R1H/2   # vertical midpoint row 1 = 2.88"

# React ↔ FastAPI
G1L = Inches(3.15); G1R = Inches(4.65)
add_rect(s, G1L, A_MID - Inches(0.14), G1R - G1L, Pt(2), ICE)
add_text(s, "→", G1R - Inches(0.22), A_MID - Inches(0.26), Inches(0.25), Inches(0.3),
         bold=True, size=12, color=ICE)
add_text(s, "REST calls", G1L, A_MID - Inches(0.37), G1R - G1L, Inches(0.22),
         size=10, color=MUTED, align=PP_ALIGN.CENTER, italic=True)
add_rect(s, G1L, A_MID + Inches(0.1), G1R - G1L, Pt(2), ICE)
add_text(s, "←", G1L - Inches(0.06), A_MID + Inches(0.0), Inches(0.25), Inches(0.3),
         bold=True, size=12, color=ICE)
add_text(s, "results", G1L, A_MID + Inches(0.17), G1R - G1L, Inches(0.22),
         size=10, color=MUTED, align=PP_ALIGN.CENTER, italic=True)

# FastAPI ↔ Claude
G2L = Inches(8.35); G2R = Inches(9.65)
add_rect(s, G2L, A_MID - Inches(0.14), G2R - G2L, Pt(2), ICE)
add_text(s, "→", G2R - Inches(0.22), A_MID - Inches(0.26), Inches(0.25), Inches(0.3),
         bold=True, size=12, color=ICE)
add_text(s, "msg + context", G2L, A_MID - Inches(0.37), G2R - G2L, Inches(0.22),
         size=10, color=MUTED, align=PP_ALIGN.CENTER, italic=True)
add_rect(s, G2L, A_MID + Inches(0.1), G2R - G2L, Pt(2), ICE)
add_text(s, "←", G2L - Inches(0.06), A_MID + Inches(0.0), Inches(0.25), Inches(0.3),
         bold=True, size=12, color=ICE)
add_text(s, "AI response", G2L, A_MID + Inches(0.17), G2R - G2L, Inches(0.22),
         size=10, color=MUTED, align=PP_ALIGN.CENTER, italic=True)

# FastAPI → Rec Engine + Product DB  (fork arrow)
FAPI_CX  = Inches(4.65) + Inches(3.7)/2   # 6.5"
FAPI_BOT = R1Y + R1H                       # 3.88"
RE_CX    = Inches(3.5)  + Inches(2.8)/2    # 4.9"
DB_CX    = Inches(6.6)  + Inches(2.8)/2    # 8.0"
FORK_Y   = FAPI_BOT + (R2Y - FAPI_BOT)/2   # 4.19"

# Stem down from FastAPI center
add_rect(s, FAPI_CX - Pt(1), FAPI_BOT, Pt(2), FORK_Y - FAPI_BOT, ICE)
# Horizontal bar at fork
add_rect(s, RE_CX, FORK_Y - Pt(1), DB_CX - RE_CX, Pt(2), ICE)
# Left branch → Rec Engine
add_rect(s, RE_CX - Pt(1), FORK_Y, Pt(2), R2Y - FORK_Y, ICE)
add_text(s, "↓", RE_CX - Inches(0.1), R2Y - Inches(0.22), Inches(0.22), Inches(0.28),
         bold=True, size=11, color=ICE, align=PP_ALIGN.CENTER)
# Right branch → Product DB
add_rect(s, DB_CX - Pt(1), FORK_Y, Pt(2), R2Y - FORK_Y, ICE)
add_text(s, "↓", DB_CX - Inches(0.1), R2Y - Inches(0.22), Inches(0.22), Inches(0.28),
         bold=True, size=11, color=ICE, align=PP_ALIGN.CENTER)

# Fork labels
add_text(s, "profile + products",
         RE_CX - Inches(1.3), FORK_Y - Inches(0.25), Inches(2.0), Inches(0.22),
         size=10, color=MUTED, italic=True)
add_text(s, "ranked list ↑",
         RE_CX - Inches(1.3), FORK_Y + Inches(0.04), Inches(2.0), Inches(0.22),
         size=10, color=MUTED, italic=True)
add_text(s, "query feasible set",
         DB_CX - Inches(0.3), FORK_Y - Inches(0.25), Inches(1.8), Inches(0.22),
         size=10, color=MUTED, italic=True)

# ETL → Product DB  (short horizontal arrow)
DB_RIGHT = Inches(6.6) + Inches(2.8)    # 9.4"
ETL_LEFT = Inches(9.7)
ETL_MID_Y = R2Y + R2H/2                 # 5.4"
add_rect(s, DB_RIGHT, ETL_MID_Y - Pt(1), ETL_LEFT - DB_RIGHT, Pt(2), ICE)
add_text(s, "←", DB_RIGHT - Inches(0.06), ETL_MID_Y - Inches(0.16), Inches(0.22), Inches(0.28),
         bold=True, size=11, color=ICE)
add_text(s, "offline feed",
         DB_RIGHT, ETL_MID_Y - Inches(0.25), ETL_LEFT - DB_RIGHT, Inches(0.22),
         size=10, color=MUTED, align=PP_ALIGN.CENTER, italic=True)

add_notes(s,
    "Architecture talking points:\n"
    "- React frontend talks to FastAPI backend over REST. The five scenes are "
    "Need Discovery, Clarification, 3 Curated Picks, Why-this-fits, Lifecycle.\n"
    "- FastAPI orchestrates Claude (language) and the Recommendation Engine "
    "(deterministic). Eight endpoints including /save and /lifecycle.\n"
    "- Claude Opus 4.6 is used at three call sites: parse free-text input, "
    "write personal product copy, parse refine intent. Each has a deterministic "
    "fallback so the demo runs without an API key — regex classifier for input, "
    "rule->text dictionary for copy, regex parser for refine.\n"
    "- Recommendation Engine is plain Python: filter, score, rank, curated 3 "
    "picks, factual tradeoff labels. It is never an LLM call. This is the "
    "trust boundary that anchors auditability.\n"
    "- Product DB is products_clean.json with 100 products across the three "
    "categories. ETL via Playwright is offline batch.")

slide_num(s, 7)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 8 — Recommendation Algorithm  (LIGHT)
# Deterministic rule-based core. Dynamic weights + two-tier scoring.
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, LIGHT_BG); top_bar(s, NAVY); bot_bar(s, NAVY)

section_label(s, "06  ·  Recommendation Algorithm", NAVY)
slide_title(s, "The Deterministic Core", NAVY, 30)
divider(s, 1.48, NAVY)

# ── Control Ownership Strip ───────────────────────────────────────────────────
cs_y = Inches(1.58); cs_h = Inches(0.42)
cs_items = [
    ("🤖  Claude — Free-Text Parsing (with regex fallback)",    MUTED),
    ("⚙️  Rule-Based — Ranking · Picks · Labels",                  ORANGE),
    ("🤖  Claude — Personal Copy (with grounded fallback)",       MUTED),
]
cs_w = Inches(4.08); cs_gap = Inches(0.08); cs_x0 = Inches(0.45)
for i, (label, fill) in enumerate(cs_items):
    cx = cs_x0 + i * (cs_w + cs_gap)
    add_rect(s, cx, cs_y, cs_w, cs_h, fill)
    add_text(s, label, cx, cs_y + Inches(0.06), cs_w, Inches(0.32),
             bold=True, size=11, color=WHITE, align=PP_ALIGN.CENTER)

# ── Left: algorithm flow ──────────────────────────────────────────────────────
SX = Inches(0.45); SW = Inches(5.75)
flow_y0 = Inches(2.18)
step_h = Inches(0.95); step_gap = Inches(0.14)
alg_steps = [
    (NAVY,     ICE,   "① Filter",
     "Apply hard constraints (budget, delivery, no-camera).\nNon-matches drop out before scoring."),
    (MID_BLUE, WHITE, "② Score",
     "General: rating · price · delivery (weights from priority)\nFeature: category rules (voice · screen · privacy · ...)"),
    (ORANGE,   WHITE, "③ Rank",
     "Combined = General + category bonus.\nSort top-N descending."),
    (TEAL,     WHITE, "④ Curate 3 Picks + Labels",
     "Best Fit · Budget Pick · Stretch.\nFactual labels (Cheapest, Most leakproof) — only when true."),
]
for i, (fill, tc, title, desc) in enumerate(alg_steps):
    sy = flow_y0 + i * (step_h + step_gap)
    add_rect(s, SX, sy, SW, step_h, fill)
    add_text(s, title, SX+Inches(0.12), sy+Inches(0.06),
             SW-Inches(0.22), Inches(0.34), bold=True, size=12, color=tc)
    add_text(s, desc, SX+Inches(0.12), sy+Inches(0.40),
             SW-Inches(0.22), Inches(0.54), size=10, color=tc)
    if i < 3:
        add_text(s, "↓", SX + SW/2 - Inches(0.1),
                 sy + step_h + step_gap/2 - Inches(0.12),
                 Inches(0.22), Inches(0.25), bold=True, size=13, color=NAVY)

# ── Right: worked example ─────────────────────────────────────────────────────
EX = Inches(6.55); EW = Inches(6.40)

# Example header
add_rect(s, EX, Inches(2.18), EW, Inches(0.46), MID_BLUE)
add_text(s, "Example — User intent: “Reliable smart display · Can wait on delivery · Budget flexible”",
         EX+Inches(0.1), Inches(2.22), EW-Inches(0.2), Inches(0.4),
         bold=True, size=10.5, color=WHITE)

# General weights panel (DYNAMIC — derived from user)
add_text(s, "GENERAL WEIGHTS  —  dynamic, derived from this user's priorities",
         EX+Inches(0.1), Inches(2.74), EW-Inches(0.2), Inches(0.22),
         bold=True, size=9, color=NAVY)
gen_chips = [("Rating", "50%", MID_BLUE), ("Price", "30%", PURPLE), ("Delivery", "20%", TEAL)]
gen_chip_w = Inches(2.0); gen_gap = Inches(0.06)
for i, (lbl, pct, col) in enumerate(gen_chips):
    cx = EX + Inches(0.1) + i * (gen_chip_w + gen_gap)
    add_rect(s, cx, Inches(3.0), gen_chip_w, Inches(0.36), col)
    add_text(s, f"{lbl}  {pct}", cx, Inches(3.02),
             gen_chip_w, Inches(0.32), bold=True, size=10, color=WHITE, align=PP_ALIGN.CENTER)

# Feature weights panel (CATEGORY-SPECIFIC)
add_text(s, "FEATURE WEIGHTS  —  category-specific  (smart displays)",
         EX+Inches(0.1), Inches(3.46), EW-Inches(0.2), Inches(0.22),
         bold=True, size=9, color=NAVY)
feat_chips = [("Voice", "40%"), ("Screen", "30%"), ("Smart Home", "20%"), ("Brand", "10%")]
feat_chip_w = Inches(1.48); feat_gap = Inches(0.06)
for i, (lbl, pct) in enumerate(feat_chips):
    cx = EX + Inches(0.1) + i * (feat_chip_w + feat_gap)
    add_rect(s, cx, Inches(3.72), feat_chip_w, Inches(0.36), RGBColor(0x2A, 0x35, 0x75))
    add_text(s, f"{lbl}  {pct}", cx, Inches(3.74),
             feat_chip_w, Inches(0.32), bold=True, size=9.5, color=ICE, align=PP_ALIGN.CENTER)

# Product rows — two-tier scores
prods = [
    (GREEN_OK, "✓  PASS",       "Amazon Echo Show 8",        "$79 · 4.7★ · 2-day",  "Gen: 85  ·  Feat: 78",  "Combined: 82   →  #1", NAVY),
    (GREEN_OK, "✓  PASS",       "Google Nest Hub (2nd Gen)", "$65 · 4.5★ · 3-day",  "Gen: 78  ·  Feat: 82",  "Combined: 80   →  #2", NAVY),
    (RED_NO,   "✗  ELIMINATED", "Amazon Echo Show 15",       "$249 · 4.8★ · 2-day", "$249 > $80 budget",     "Eliminated before scoring", RED_NO),
]
row_h = Inches(0.72); row_gap = Inches(0.06)
prod_y0 = Inches(4.20)
for i, (badge_col, badge, name, attrs, score, combined, ccol) in enumerate(prods):
    py = prod_y0 + i * (row_h + row_gap)
    row_fill = RGBColor(0xF0,0xF4,0xFF) if i % 2 == 0 else LIGHT_BG
    add_rect(s, EX, py, EW, row_h, row_fill)
    add_rect(s, EX, py, Inches(1.2), row_h, badge_col)
    add_text(s, badge, EX+Inches(0.02), py+Inches(0.22),
             Inches(1.16), Inches(0.3), bold=True, size=9, color=WHITE, align=PP_ALIGN.CENTER)
    add_text(s, name, EX+Inches(1.3), py+Inches(0.04),
             Inches(3.0), Inches(0.3), bold=True, size=10.5, color=DARK_TEXT)
    add_text(s, attrs, EX+Inches(1.3), py+Inches(0.36),
             Inches(3.0), Inches(0.26), size=9, color=MUTED)
    add_text(s, score, EX+Inches(4.3), py+Inches(0.06),
             Inches(2.0), Inches(0.3), size=9.5, color=DARK_TEXT, align=PP_ALIGN.RIGHT)
    add_text(s, combined, EX+Inches(4.3), py+Inches(0.36),
             Inches(2.0), Inches(0.3), bold=True, size=10, color=ccol, align=PP_ALIGN.RIGHT)

# ── Full-width bottom insight bar ─────────────────────────────────────────────
add_rect(s, Inches(0.45), Inches(6.55), Inches(12.4), Inches(0.5), NAVY)
add_text(s,
         "When the system must decide what to show the user, AI steps aside.  "
         "Ranking is rule-based, reproducible, and auditable — trust is anchored here.",
         Inches(0.55), Inches(6.58), Inches(12.2), Inches(0.44),
         bold=True, size=11, color=ICE, align=PP_ALIGN.CENTER)

add_notes(s,
    "Algorithm walkthrough (worked example):\n"
    "User intent: 'Reliable smart display, can wait on delivery, budget flexible'.\n"
    "GENERAL WEIGHTS (dynamic, derived from user priority): "
    "rating 50%, price 30%, delivery 20%.\n"
    "FEATURE WEIGHTS (smart_display): voice 40%, screen 30%, smart-home 20%, "
    "brand 10%.\n"
    "PRODUCTS:\n"
    "  Echo Show 8 ($79, 4.7 stars, 2-day) -> Gen 85 / Feat 78 / Combined 82 -> #1\n"
    "  Nest Hub 2nd Gen ($65, 4.5 stars, 3-day) -> Gen 78 / Feat 82 / Combined 80 -> #2\n"
    "  Echo Show 15 ($249) eliminated by $80 budget filter before scoring.\n"
    "Trust-boundary anchor: when the system must decide what to show, AI steps "
    "aside. Ranking is rule-based, reproducible, and auditable.")

slide_num(s, 8, dark=False)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 9 — Supporting Stack  (LIGHT)
# What feeds the decision engine: ETL · Schema · Claude call sites · Frontend
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, LIGHT_BG); top_bar(s, NAVY); bot_bar(s, NAVY)

section_label(s, "07  ·  Data, AI & Frontend", NAVY)
slide_title(s, "The Supporting Stack — What Feeds the Decision Engine", NAVY, 28)
divider(s, 1.62, NAVY)

stack_cards = [
    ("ETL  +  Provenance Flags",  MID_BLUE,
     "Playwright scrapers  ·  Amazon · Target\n"
     "Anti-bot stealth · normalize · dedup\n"
     "Each field flagged: scraped vs estimated\n"
     "vs synthesised — no silent fabrication",
     "100 products  ·  3 categories"),
    ("Attribute Extraction",  TEAL,
     "screen_inches · ecosystems · has_camera\n"
     "mounting · capacity_oz · bottle_material\n"
     "drinking_style · organiser_material\n"
     "Pulled from titles at load time",
     "feeds ranker, picks, compare view"),
    ("Claude Opus 4.6  —  3 Call Sites",  PURPLE,
     "①  Parse free-text input\n"
     "②  Write personal product copy\n"
     "③  Parse refine intent\n"
     "Every call has a deterministic fallback",
     "Never on the ranking path"),
    ("React Frontend  —  5 Stages",  ORANGE,
     "①  Need Discovery\n"
     "②  Clarification Q&A\n"
     "③  3 Curated Picks\n"
     "④  Why This Fits  (rule-grounded checklist)\n"
     "⑤  Lifecycle  (prototype value-extension)",
     "+ Compare overlay · Save-for-later · Diff"),
]

positions = [
    (Inches(0.45), Inches(1.82)),
    (Inches(6.78), Inches(1.82)),
    (Inches(0.45), Inches(4.42)),
    (Inches(6.78), Inches(4.42)),
]
card_w = Inches(6.10); card_h = Inches(2.48)

for (x, y), (title, fill, body, badge) in zip(positions, stack_cards):
    add_rect(s, x, y, card_w, card_h, fill)
    add_text(s, title, x + Inches(0.15), y + Inches(0.08),
             card_w - Inches(0.25), Inches(0.42),
             bold=True, size=13, color=ICE)
    add_text(s, body, x + Inches(0.15), y + Inches(0.52),
             card_w - Inches(0.25), Inches(1.55), size=10.5, color=WHITE)
    add_rect(s, x + Inches(0.12), y + card_h - Inches(0.34),
             card_w - Inches(0.25), Inches(0.28), NAVY)
    add_text(s, badge, x + Inches(0.22), y + card_h - Inches(0.33),
             card_w - Inches(0.4), Inches(0.26),
             bold=True, size=9, color=ICE)

add_notes(s,
    "Supporting stack — talking points:\n"
    "ETL: scrapes 100 products via Playwright with anti-bot measures, normalises "
    "delivery copy ('arrives Mar 14' -> 5 days). 72/100 delivery values were "
    "missing post-scrape and are flagged 'estimated'; descriptions for all 100 "
    "are flagged 'synthesised from title'. No silent fabrication.\n\n"
    "Attribute extraction: regex-based, runs at load time. Echo Show models map "
    "to known screen sizes (5 -> 5.5\", 8 -> 8\", 15 -> 15.6\"); ecosystems "
    "infer from Echo/Nest/HomePod keywords; bottle capacity from 'oz' patterns.\n\n"
    "Claude call sites in the runtime: parse free-text input, write personal "
    "copy, parse refine intent. All three have deterministic fallbacks so the "
    "demo runs without an API key. Ranking is never an LLM call.\n\n"
    "AI tooling across the build (disclosed honestly):\n"
    "- Runtime model:  Claude Opus 4.6 (anthropic SDK).\n"
    "- Pair-programming:  Claude Code agent on Opus 4.6 and 4.7 across the "
    "12-week build.\n"
    "- Independent validation:  Codex GPT-5.5 was run as an independent "
    "technical reviewer to flag demo-safety issues.\n"
    "All three are named in the report's AI Contributions section.")

# Bottom disclosure strip — same visual style as the bridge bar on slide 4.
# Acknowledges the multi-model workflow explicitly so the runtime model on
# the Claude card isn't read as the only AI tool used in the project.
add_rect(s, Inches(0.45), Inches(7.05), Inches(12.4), Inches(0.36), NAVY)
add_text(s,
         "AI tooling:  Runtime  Claude Opus 4.6   ·   Build  Claude Code (Opus 4.6 / 4.7)"
         "   ·   Independent validation  Codex GPT-5.5",
         Inches(0.6), Inches(7.07), Inches(12.1), Inches(0.32),
         bold=True, size=10, color=ICE, align=PP_ALIGN.CENTER)

slide_num(s, 9, dark=False)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 10 — Results & Demo  (DARK)
# Fix: strengthened results — added evaluation outcomes, not just impl metrics
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, NAVY); top_bar(s, ICE); bot_bar(s, ICE)

section_label(s, "08  ·  Results & Demo")
slide_title(s, "Capability Validation & Scenario Walkthrough")
divider(s, 1.62)

# Left — evaluation findings (the real results)
add_rect(s, Inches(0.5), Inches(1.82), Inches(6.2), Inches(4.8), MID_BLUE)
add_text(s, "Capability Validation",
         Inches(0.65), Inches(1.95), Inches(5.9), Inches(0.42),
         bold=True, size=13, color=ICE)

findings = [
    ("Capability gaps (self-evaluation)",
     "7 of 7 gaps addressed in our walkthroughs;\nno surveyed platform addressed more than 2"),
    ("Decision-critical attributes inline",
     "Screen size, ecosystem, camera, capacity,\nmaterial — surfaced on every pick"),
    ("End-to-end in five scenes",
     "Need → clarify → 3 picks → why-this-fits →\nlifecycle. Zero external page navigation."),
    ("Trade-offs visible, not hidden",
     "Every pick shows a ✓/✗/? checklist mapping\nyour chips to match status — no surprises"),
]
for i, (title, body) in enumerate(findings):
    y = Inches(2.5) + i * Inches(1.0)
    add_text(s, f"✓  {title}", Inches(0.65), y,
             Inches(5.9), Inches(0.38), bold=True, size=11, color=GREEN_OK)
    add_text(s, body, Inches(0.65), y + Inches(0.36),
             Inches(5.9), Inches(0.55), size=10, color=WHITE)

# Right — demo walkthrough (water-bottle scenario showcases the new
# preference checklist, curated picks, refine, and comparison features)
add_rect(s, Inches(6.95), Inches(1.82), Inches(5.9), Inches(4.8), RGBColor(0x2A,0x35,0x75))
add_text(s, "Demo — Water-Bottle Scenario",
         Inches(7.1), Inches(1.95), Inches(5.6), Inches(0.42),
         bold=True, size=12, color=ICE)

demo_steps = [
    ("①  Need Discovery",
     "“Current bottle is heavy and leaks\nin my gym bag.”  → water_bottle"),
    ("②  Clarification (3 chips)",
     "Gym · Large capacity · (leak inferred\nfrom 'leaks' in the input)"),
    ("③  3 Curated Picks",
     "Best Fit  Owala 24oz FreeSip\nrules: gym_suitable · large_capacity_pref · leak_proof_match"),
    ("④  Picks — labels + checklist",
     "Budget Pick: Zak 19oz [Cheapest · Most portable]\nStretch: Owala 32oz [Most capacity · Most leakproof]"),
    ("⑤  Refine + Compare",
     "‘larger’ → flips Best Fit to 32oz · diff card shown\nSelect 3, compare side-by-side with row-winners"),
]
step_h = Inches(0.85)
for i, (step, desc) in enumerate(demo_steps):
    y = Inches(2.45) + i * step_h
    add_text(s, step, Inches(7.1), y,
             Inches(5.6), Inches(0.32), bold=True, size=10.5, color=ICE)
    add_text(s, desc, Inches(7.1), y + Inches(0.30),
             Inches(5.6), Inches(0.55), size=9.5, color=WHITE)

# Honest caveat footer — this is self-assessment, not a user study
add_rect(s, Inches(0.5), Inches(6.78), Inches(11.45), Inches(0.42),
         RGBColor(0x2A, 0x35, 0x75))
add_text(s,
         "Heuristic self-assessment against the seven capability gaps in our evaluation  ·  "
         "formal user study is future work (see Slide 11)",
         Inches(0.5), Inches(6.82), Inches(11.45), Inches(0.36),
         size=10, color=ICE, italic=True, align=PP_ALIGN.CENTER)

add_notes(s,
    "Live demo script (matches the running app exactly):\n\n"
    "1. Type into Scene 1: 'current bottle is heavy and leaks in my gym bag'.\n"
    "   Observe: category auto-classified as water_bottle. The route also "
    "infers leak_proof_preferred=True from the word 'leaks'.\n\n"
    "2. Scene 2: pick three chips — Water Bottle / Gym / Large capacity. "
    "Skip the others. Hit 'See recommendations'.\n\n"
    "3. Scene 3: three differentiated picks render in a row.\n"
    "   - BEST FIT: Owala 24oz FreeSip — rules [gym_suitable, "
    "large_capacity_pref, leak_proof_match]. The Large-capacity preference "
    "is honoured (≥24oz) and leak-resistance is matched.\n"
    "   - BUDGET PICK: Zak Designs 19oz — labels [Cheapest, Most portable]. "
    "Honestly shows ✗ Large capacity (19oz) in its checklist.\n"
    "   - LARGE CAPACITY PICK: Owala 32oz FreeSip — labels [Most capacity, "
    "Most leakproof].\n\n"
    "4. Click 'See why' on Best Fit. Stage 4 quotes the user's frustration, "
    "lists the rule-grounded reasons, and shows the ✓/✗/? checklist of every "
    "preference.\n\n"
    "5. Refine: type 'larger'. The diff card shows size_preference None -> "
    "large; Best Fit flips to 32oz. Demonstrates preference continuity.\n\n"
    "6. Click compare on 2-3 picks; the side-by-side overlay highlights the "
    "row-winner (lowest price, largest capacity, etc.) per attribute.\n\n"
    "7. Continue to Lifecycle (prototype). Phone reminders / gym-bag checklist "
    "/ replacement parts — honest about what the bottle can/cannot do.")

slide_num(s, 10)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 11 — Limitations, Conclusions & Future Work  (LIGHT)
# Fix: conclusion wording — "designed to address" not "reduces" (unmeasured)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, LIGHT_BG); top_bar(s, NAVY); bot_bar(s, NAVY)

section_label(s, "09  ·  Limitations, Conclusions & Future Work", NAVY)
slide_title(s, "Honest Assessment · What This Proves · Next Steps", NAVY, 28)
divider(s, 1.62, NAVY)

col3_w = Inches(4.0); col3_gap = Inches(0.25)
col3_x = [
    Inches(0.45),
    Inches(0.45) + col3_w + col3_gap,
    Inches(0.45) + 2 * (col3_w + col3_gap),
]
col3_y = Inches(1.82); col3_h = Inches(5.25)
col_titles  = ["Limitations",        "Conclusions & Impact",  "Future Work"]
col_colors  = [RGBColor(0x6B,0x25,0x25), MID_BLUE,            TEAL]

for x, title, fill in zip(col3_x, col_titles, col_colors):
    add_rect(s, x, col3_y, col3_w, col3_h, fill)
    add_text(s, title, x + Inches(0.12), col3_y + Inches(0.1),
             col3_w - Inches(0.22), Inches(0.42),
             bold=True, size=12, color=WHITE)

lims = [
    "⚠  Small dataset — 100 products,\n    3 categories only",
    "⚠  No formal user study —\n    heuristic evaluation only",
    "⚠  72/100 delivery values are\n    estimated (flagged in data)",
    "⚠  Rule-based ranking — weights\n    inferred, not learned",
]
# Fixed: "designed to address" not "reduces" (no user study to prove it)
cons = [
    "✓  Decision support feasible\n    end-to-end without an LLM key",
    "✓  Explanations grounded in the\n    same rules the ranker used",
    "✓  Visible preference continuity —\n    every refine shows a diff",
    "✓  Lifecycle layer is a prototype\n    value-extension concept",
    "✓  Multi-model workflow disclosed:\n    Opus 4.6 + 4.7 build · Codex 5.5 review",
]
fut = [
    "→  Formal user study\n    (SUS, task completion time)",
    "→  Live retailer API\n    for real-time pricing",
    "→  ML-based ranking\n    from interaction data",
    "→  Expand to more\n    product categories",
    "→  Mobile-first UI\n    redesign",
]

for i, txt in enumerate(lims):
    add_text(s, txt, col3_x[0] + Inches(0.12),
             col3_y + Inches(0.65) + i * Inches(0.88),
             col3_w - Inches(0.22), Inches(0.8),
             size=10, color=WHITE)

for i, txt in enumerate(cons):
    add_text(s, txt, col3_x[1] + Inches(0.12),
             col3_y + Inches(0.65) + i * Inches(0.88),
             col3_w - Inches(0.22), Inches(0.8),
             size=10, color=WHITE)

for i, txt in enumerate(fut):
    add_text(s, txt, col3_x[2] + Inches(0.12),
             col3_y + Inches(0.65) + i * Inches(0.88),
             col3_w - Inches(0.22), Inches(0.8),
             size=10, color=WHITE)

slide_num(s, 11, dark=False)

# ══════════════════════════════════════════════════════════════════════════════
# SLIDE 12 — Thank You / Q&A  (DARK)
# ══════════════════════════════════════════════════════════════════════════════
s = prs.slides.add_slide(BL)
bg(s, NAVY); top_bar(s, ICE); bot_bar(s, ICE)

add_text(s, "Thank You",
         Inches(1.0), Inches(1.2), Inches(11.3), Inches(1.5),
         bold=True, size=60, color=WHITE, align=PP_ALIGN.CENTER)
add_text(s, "Questions & Discussion",
         Inches(1.0), Inches(2.7), Inches(11.3), Inches(0.7),
         size=22, color=ICE, align=PP_ALIGN.CENTER)

r = s.shapes.add_shape(1, Inches(1.0), Inches(3.6), Inches(11.3), Pt(1.5))
r.fill.solid(); r.fill.fore_color.rgb = ICE; r.line.fill.background()

info_items = [
    ("Author",       "Chenghui Tan"),
    ("Institution",  "California State University, East Bay (CSUEB)"),
    ("Project",      "Decision-Oriented Conversational Shopping Assistant"),
    ("Runtime",      "React · FastAPI · Claude Opus 4.6 · Python · Playwright (ETL)"),
    ("Built with",   "Claude Code (Opus 4.6 / 4.7)  ·  Codex GPT-5.5  (independent validation)"),
]
for i, (label, value) in enumerate(info_items):
    y = Inches(3.75) + i * Inches(0.6)
    add_text(s, label + ":", Inches(2.2), y, Inches(2.2), Inches(0.6),
             bold=True, size=13, color=ICE)
    add_text(s, value, Inches(4.6), y, Inches(8.0), Inches(0.6),
             size=13, color=WHITE)

slide_num(s, 12)

# ── Save ──────────────────────────────────────────────────────────────────────
out = "/Users/sabrina/Projects/shopping-assistant-4/docs/capstone_presentation_v5.pptx"
prs.save(out)
print(f"Saved → {out}  ({len(prs.slides)} slides)")
