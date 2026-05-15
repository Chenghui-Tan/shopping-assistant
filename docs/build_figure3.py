"""
Generate Figure 3 — empirical combined-score distribution per scripted scenario.

Replaces the colorful matplotlib-default version with a monochrome chart
matching Figures 1 and 2's LaTeX-academic style: single gray bars, red
Top-1 line, dashed Top-5 cutoff.

Run: python docs/build_figure3.py
Output: docs/results_score_distribution.png
"""
import os, sys
import matplotlib.pyplot as plt
from matplotlib import rcParams

# Make the engine importable from this script.
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(PROJECT, "recommendation_Algorithem"))
sys.path.insert(0, os.path.join(PROJECT, "backend"))

import recommendation_engine_refactored as eng  # noqa: E402

OUT_PATH = os.path.join(os.path.dirname(__file__), "results_score_distribution.png")

# Use serif body to match Figures 1 and 2.
rcParams["font.family"] = "serif"
rcParams["font.serif"]  = ["Times New Roman", "Times", "DejaVu Serif"]
rcParams["axes.spines.top"]   = False
rcParams["axes.spines.right"] = False

BAR_GRAY   = "#707070"
EDGE_WHITE = "white"
TOP1_RED   = "#c0382b"
CUTOFF_K   = "#000000"

# Three scripted scenarios — same as the report's §5.1 table.
SCENARIOS = [
    {
        "name":  "Kitchen cooking",
        "prefs": {
            "category":     "smart_display",
            "use_case":     ["cooking", "family"],
            "voice_ecosystem": "alexa",
            "placement":    "kitchen",
            "screen_size_priority": "mid",
            "privacy_camera": "any",
            "price_max":    250,
            "priority":     "balanced",
        },
    },
    {
        "name":  "Gym hydration",
        "prefs": {
            "category":        "water_bottle",
            "use_case":        "gym",
            "insulated":       True,
            "material_preference": "stainless",
            "drinking_style":  "freesip",
            "size_preference": "lightweight",
            "leak_proof_preferred": True,
            "price_max":       40,
            "priority":        "balanced",
        },
    },
    {
        "name":  "Cabinet organization",
        "prefs": {
            "category":         "kitchen_organizer",
            "use_area":         "cabinet",
            "pain_point":       "not_enough_space",
            "structure_type":   "stackable",
            "organizer_material": "plastic",
            "visibility_priority": "clear",
            "price_max":        40,
            "priority":         "balanced",
        },
    },
]


def collect_scores(scenario):
    """Run the engine and return (all_scores, top1, top5_cutoff)."""
    prefs = scenario["prefs"]
    products, _relax = eng.recommend_with_relaxation(prefs, top_n=200)
    scores = sorted([p.get("_score") or 0.0 for p in products], reverse=True)
    if not scores:
        return [], 0.0, 0.0
    top1     = scores[0]
    top5_cut = scores[4] if len(scores) >= 5 else scores[-1]
    return scores, top1, top5_cut


def main():
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.2), dpi=200)
    plt.subplots_adjust(left=0.06, right=0.985, top=0.88, bottom=0.16,
                        wspace=0.32)

    for ax, sc in zip(axes, SCENARIOS):
        scores, top1, top5 = collect_scores(sc)
        ax.hist(scores, bins=15,
                color=BAR_GRAY, edgecolor=EDGE_WHITE, linewidth=0.6)
        ax.axvline(top1,  color=TOP1_RED,  linewidth=1.6,
                   label=f"Top-1: {top1:.2f}")
        ax.axvline(top5,  color=CUTOFF_K,  linewidth=1.2, linestyle="--",
                   label=f"Top-5 cutoff: {top5:.2f}")
        ax.set_title(sc["name"], fontsize=12, fontweight="bold")
        ax.set_xlabel("Combined score", fontsize=10)
        ax.set_ylabel("# products",     fontsize=10)
        ax.tick_params(axis="both", labelsize=9)
        # Order legend entries so Top-1 (the red line) reads first.
        handles, labels = ax.get_legend_handles_labels()
        order = sorted(range(len(labels)),
                       key=lambda i: 0 if labels[i].startswith("Top-1") else 1)
        ax.legend([handles[i] for i in order],
                  [labels[i]  for i in order],
                  fontsize=8.5, frameon=True, framealpha=0.9,
                  edgecolor="#cccccc", loc="upper left")

    plt.savefig(OUT_PATH, dpi=200, bbox_inches="tight",
                pad_inches=0.12, facecolor="white")
    plt.close(fig)
    print(f"saved {OUT_PATH}")


if __name__ == "__main__":
    main()
