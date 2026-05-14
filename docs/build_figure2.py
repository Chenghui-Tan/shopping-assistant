"""
Generate Figure 2 — runtime components and communication paths.

Replaces the cropped LaTeX raster from the v6 reference report with a
code-aligned matplotlib version. Re-render with:

    python docs/build_figure2.py

Output: docs/figures/figure2_runtime.png

Edit the BOXES / ARROWS lists below when the system changes. The figure
will regenerate to match.
"""
import os
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib import rcParams

rcParams["font.family"] = "serif"
rcParams["font.serif"]  = ["Times New Roman", "Times", "DejaVu Serif"]

OUT_PATH = os.path.join(os.path.dirname(__file__), "figures", "figure2_runtime.png")

# ─── Layout (figure coordinate space is 0..160 wide, 0..100 tall) ───────────
# Wider canvas + smaller boxes + larger gaps so arrow labels have a place
# to live without crashing into box content.
fig, ax = plt.subplots(figsize=(13, 6.5))
ax.set_xlim(0, 160); ax.set_ylim(0, 100)
ax.set_aspect("equal")
ax.axis("off")

# Box centres are 50 units apart horizontally, leaving an 18-unit gap for
# arrow labels (REST calls / msg + context). Top y=78, bottom y=18.
TOP_Y    = 78
BOT_Y    = 18
W        = 32     # box width
H_TOP    = 30
H_BOT    = 24
COLS     = [22, 80, 138]   # column centres for top + bottom rows

BOXES = [
    # Top row
    dict(cx=COLS[0], cy=TOP_Y, w=W, h=H_TOP, title="React Frontend",
         body=["Stage 1 — Need Discovery",
               "Stage 2 — Clarification",
               "Stage 3 — Recommendations",
               "Stage 4 — Why-this-fits",
               "Stage 5 — Lifecycle"], shade=False),
    dict(cx=COLS[1], cy=TOP_Y, w=W, h=H_TOP, title="FastAPI Backend",
         body=["/start  /answer  /recommend",
               "/refine  /{id}/lifecycle",
               "Orchestrates Claude,",
               "ranking, and product DB"], shade=True),
    dict(cx=COLS[2], cy=TOP_Y, w=W, h=H_TOP, title="Claude Opus 4.7 (AI)",
         body=["Parse preferences",
               "Clarifying questions",
               "Explain trade-offs"], shade=False),
    # Bottom row
    dict(cx=COLS[0], cy=BOT_Y, w=W, h=H_BOT, title="Recommendation Engine",
         body=["Weighted scoring",
               "Hard constraint filter",
               "Deterministic — no AI"], shade=False),
    dict(cx=COLS[1], cy=BOT_Y, w=W, h=H_BOT, title="Product DB",
         body=["products_clean.json",
               "100 products, 3 categories",
               "Smart display / water bottle /",
               "kitchen organizer"], shade=False),
    dict(cx=COLS[2], cy=BOT_Y, w=W, h=H_BOT, title="ETL Pipeline",
         body=["Playwright scrapers",
               "Amazon, Target",
               "Normalize & deduplicate",
               "Offline batch feed"], shade=False),
]

# ─── Draw boxes ──────────────────────────────────────────────────────────────
for b in BOXES:
    x = b["cx"] - b["w"] / 2
    y = b["cy"] - b["h"] / 2
    patch = FancyBboxPatch(
        (x, y), b["w"], b["h"],
        boxstyle="round,pad=0.4,rounding_size=0.4",
        linewidth=1.2,
        edgecolor="black",
        facecolor="#f0f0f0" if b["shade"] else "white",
    )
    ax.add_patch(patch)
    # Title (bold)
    ax.text(b["cx"], b["cy"] + b["h"]/2 - 2.2, b["title"],
            ha="center", va="top", fontsize=10.5, fontweight="bold")
    # Body lines below title
    line_h = (b["h"] - 5.5) / max(len(b["body"]), 1)
    body_top = b["cy"] + b["h"]/2 - 6.2
    for i, line in enumerate(b["body"]):
        is_mono = "/session/" in line or "products_clean.json" in line
        ax.text(b["cx"], body_top - i * line_h, line,
                ha="center", va="top",
                fontsize=8.5,
                family="monospace" if is_mono else "serif")


# ─── Arrows ──────────────────────────────────────────────────────────────────
def arrow(x1, y1, x2, y2, label="", label_xy=None, dashed=False,
          rad=0.0, fontsize=9):
    style = dict(arrowstyle="-|>", mutation_scale=14,
                 linewidth=1.1, color="black")
    if dashed:
        style["linestyle"] = (0, (4, 3))
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2),
                                 connectionstyle=f"arc3,rad={rad}",
                                 **style))
    if label:
        lx, ly = label_xy if label_xy else ((x1 + x2)/2, (y1 + y2)/2 + 1.2)
        ax.text(lx, ly, label, ha="center", va="center",
                fontsize=fontsize, style="italic",
                bbox=dict(facecolor="white", edgecolor="none",
                          pad=0.6))


# Edge coordinates per column / row (cx ± W/2, cy ± H/2):
#   Top row    : right edge cx+16,  left edge cx-16,  top y=93,  bottom y=63
#   Bottom row : right edge cx+16,  left edge cx-16,  top y=30,  bottom y=6
LEFT_TOP, MID_TOP, RIGHT_TOP    = COLS
LEFT_BOT, MID_BOT, RIGHT_BOT    = COLS
LBL_FS = 9

# Frontend ↔ FastAPI (top-row horizontal pair)
arrow(LEFT_TOP + 16, TOP_Y + 4, MID_TOP - 16, TOP_Y + 4, "REST calls",
      label_xy=((LEFT_TOP + MID_TOP)/2, TOP_Y + 8), fontsize=LBL_FS)
arrow(MID_TOP - 16,  TOP_Y - 4, LEFT_TOP + 16, TOP_Y - 4, "results",
      label_xy=((LEFT_TOP + MID_TOP)/2, TOP_Y - 8), fontsize=LBL_FS)

# FastAPI ↔ Claude
arrow(MID_TOP + 16,   TOP_Y + 4, RIGHT_TOP - 16, TOP_Y + 4, "msg + context",
      label_xy=((MID_TOP + RIGHT_TOP)/2, TOP_Y + 8), fontsize=LBL_FS)
arrow(RIGHT_TOP - 16, TOP_Y - 4, MID_TOP + 16,   TOP_Y - 4, "AI response",
      label_xy=((MID_TOP + RIGHT_TOP)/2, TOP_Y - 8), fontsize=LBL_FS)

# FastAPI → Recommendation Engine (down-left diagonal)
arrow(MID_TOP - 6,  TOP_Y - 15, LEFT_BOT + 6,  BOT_Y + 12,
      "profile + products",
      label_xy=((MID_TOP + LEFT_BOT)/2 - 4, (TOP_Y + BOT_Y)/2 + 4),
      fontsize=LBL_FS)

# FastAPI → Product DB (straight down)
arrow(MID_TOP, TOP_Y - 15, MID_BOT, BOT_Y + 12, "query feasible set",
      label_xy=(MID_TOP + 11, (TOP_Y + BOT_Y)/2), fontsize=LBL_FS)

# ETL → Product DB (right-to-left, dashed)
arrow(RIGHT_BOT - 16, BOT_Y, MID_BOT + 16, BOT_Y, "offline feed",
      label_xy=((RIGHT_BOT + MID_BOT)/2, BOT_Y + 5),
      dashed=True, fontsize=LBL_FS)

# ─── Save ────────────────────────────────────────────────────────────────────
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
plt.savefig(OUT_PATH, dpi=200, bbox_inches="tight",
            pad_inches=0.15, facecolor="white")
print(f"saved {OUT_PATH}")
