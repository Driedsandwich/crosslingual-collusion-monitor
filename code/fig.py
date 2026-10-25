"""Figures for the report from runs/results.json (and optionally runs/results_batch.json).

Written during the sprint (2026-10-26). Palette: six categorical slots validated with the dataviz validator (light mode);
each monitor also gets its own marker shape so identity never rests on colour alone. Exact numbers are in the report tables.
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import llm

ORDER = ["en", "en_ind", "ja", "ja_ind", "ja_idiom", "bt_ja", "bt_ja_ind", "bt_ja_idiom"]
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]
SHORT = {"mistral-small-2603": "Mistral Small", "ministral-8b-2512": "Ministral 8B", "zai-glm-5-3-flash": "GLM-5.3 Flash",
         "deepseek-ai/DeepSeek-V4.1-Flash-1017": "DeepSeek V4.1 Flash", "openai/gpt-oss-120b": "gpt-oss-120b",
         "google/gemma-4-31B-it": "Gemma 4 31B", "batch:gpt-6.1-sol": "GPT-6.1 Sol (batch)", "batch:grok-4.7": "Grok 4.7 (batch)"}
INK, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"


def style(ax):
    ax.set_facecolor(SURF)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)
    ax.tick_params(colors=MUTED, labelsize=8)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)


def panel(ax, res, key, ylabel, monitors, ci=True, field="tpr"):
    n = len(monitors)
    for k, m in enumerate(monitors):
        xs, ys, lo, hi = [], [], [], []
        for j, v in enumerate(ORDER):
            e = res[key].get(f"{m}|{v}")
            if e is None:
                continue
            off = (k - (n - 1) / 2) * 0.09
            xs.append(j + off)
            if key == "auc":
                ys.append(e["auc"]); lo.append(e["auc"] - e["lo"]); hi.append(e["hi"] - e["auc"])
            else:
                ys.append(e[field])
        kw = dict(color=COLORS[k], marker=MARKERS[k], markersize=5.5, linestyle="none", label=SHORT.get(m, m),
                  markeredgecolor=SURF, markeredgewidth=0.8)
        if key == "auc" and ci:
            ax.errorbar(xs, ys, yerr=[lo, hi], elinewidth=1.0, capsize=0, **kw)
        else:
            ax.plot(xs, ys, **kw)
    ax.set_xticks(range(len(ORDER)))
    ax.set_xticklabels(ORDER, rotation=0, fontsize=7.5, color=INK)
    ax.set_ylabel(ylabel, fontsize=8.5, color=INK)
    ax.axvspan(4.5, 7.5, color="#f0efec", zorder=0)
    style(ax)


def main(res_path, out_png, title_suffix=""):
    res = json.loads(Path(res_path).read_text())
    monitors = sorted({k.split("|")[0] for k in res["auc"]}, key=lambda m: list(SHORT).index(m) if m in SHORT else 99)
    fig, axes = plt.subplots(2, 1, figsize=(6.2, 3.0), dpi=200, facecolor=SURF)
    panel(axes[0], res, "rates", "Detection rate\n(collusive chats)", monitors, ci=False, field="tpr")
    axes[0].set_ylim(-0.03, 1.03)
    panel(axes[1], res, "rates", "False-alarm rate\n(hard negatives)", monitors, ci=False,
          field="fpr_hardneg")
    axes[1].set_ylim(-0.03, 1.03)
    axes[0].legend(fontsize=7, ncol=3, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0))
    axes[0].text(6, 0.5, "back-translated", ha="center", fontsize=7, color=MUTED)
    fig.tight_layout()
    fig.savefig(out_png, facecolor=SURF)
    print("wrote", out_png)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(llm.RUNS / "results.json"),
         sys.argv[2] if len(sys.argv) > 2 else str(llm.RUNS.parent / "report" / "fig_auc_tpr.png"))
