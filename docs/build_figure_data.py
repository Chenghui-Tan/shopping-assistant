"""
Figure 1 — Exploratory catalog summary for §3 Data Description.

Three monochrome subplots matching the academic style of Figures 2-4:
- Price distribution per category (box plot)
- Rating distribution per category (box plot)
- Review-count distribution per category (box plot, log scale)

Run: python docs/build_figure_data.py
Output: docs/results_catalog_summary.png
"""
import os, json
from collections import defaultdict
import matplotlib.pyplot as plt
from matplotlib import rcParams

PROJECT  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA     = os.path.join(PROJECT, "data", "clean", "products_clean.json")
OUT_PATH = os.path.join(os.path.dirname(__file__), "results_catalog_summary.png")

rcParams["font.family"]       = "serif"
rcParams["font.serif"]        = ["Times New Roman", "Times", "DejaVu Serif"]
rcParams["axes.spines.top"]   = False
rcParams["axes.spines.right"] = False

LABEL = {"smart_display":     "Smart\nDisplay",
         "water_bottle":      "Water\nBottle",
         "kitchen_organizer": "Kitchen\nOrganizer"}
ORDER = ["smart_display", "water_bottle", "kitchen_organizer"]

BOX_GRAY  = "#707070"
EDGE_DARK = "#303030"


def _box(ax, series, title, ylabel, *, log=False):
    data = [series[c] for c in ORDER]
    bp = ax.boxplot(data,
                    patch_artist=True,
                    widths=0.55,
                    medianprops=dict(color=EDGE_DARK, linewidth=1.6),
                    boxprops=dict(facecolor=BOX_GRAY, edgecolor=EDGE_DARK, linewidth=0.8),
                    whiskerprops=dict(color=EDGE_DARK, linewidth=0.8),
                    capprops=dict(color=EDGE_DARK, linewidth=0.8),
                    flierprops=dict(marker="o", markerfacecolor="white",
                                    markeredgecolor=EDGE_DARK, markersize=3.5))
    ax.set_xticks(range(1, len(ORDER) + 1))
    ax.set_xticklabels([LABEL[c] for c in ORDER], fontsize=9)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.set_title(title, fontsize=12, fontweight="bold")
    if log:
        ax.set_yscale("log")
    ax.tick_params(axis="both", labelsize=9)


def main():
    raw = json.load(open(DATA))
    prices, ratings, reviews = defaultdict(list), defaultdict(list), defaultdict(list)
    for p in raw:
        c = p.get("category")
        if c not in LABEL:
            continue
        if isinstance(p.get("price"), (int, float)) and p["price"]:
            prices[c].append(p["price"])
        if isinstance(p.get("rating"), (int, float)):
            ratings[c].append(p["rating"])
        if isinstance(p.get("review_count"), (int, float)):
            reviews[c].append(p["review_count"])

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), dpi=200)
    plt.subplots_adjust(left=0.06, right=0.985, top=0.88, bottom=0.16, wspace=0.32)

    _box(axes[0], prices,  "Price (USD)",          "Price ($)")
    _box(axes[1], ratings, "Average rating",       "Rating (1-5)")
    _box(axes[2], reviews, "Review count",         "Reviews (log)", log=True)

    plt.savefig(OUT_PATH, dpi=200, bbox_inches="tight",
                pad_inches=0.12, facecolor="white")
    plt.close(fig)
    print(f"saved {OUT_PATH}")


if __name__ == "__main__":
    main()
