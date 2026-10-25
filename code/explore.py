"""Exploratory analyses (not pre-specified in PROTOCOL.md; labelled exploratory in the report).

Written during the sprint (2026-10-26). For each monitor x view: mean score per class, AUC of collude vs benign only and
collude vs hardneg only. Reads the same score files as analyze.py; writes runs/explore.json.
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

import llm
from analyze import VIEWS, auc, load_scores


def main(scores, out):
    S, cls = load_scores(scores)
    res = {}
    for (m, v), sc in sorted(S.items()):
        by = defaultdict(list)
        for i, s in sc.items():
            by[cls[i]].append(s)
        res[f"{m}|{v}"] = {
            "mean": {c: round(float(np.mean(x)), 1) for c, x in by.items()},
            "auc_vs_benign": round(auc(by["collude"], by["benign"]), 3),
            "auc_vs_hardneg": round(auc(by["collude"], by["hardneg"]), 3),
            "n": {c: len(x) for c, x in by.items()},
        }
    Path(out).write_text(json.dumps(res, indent=1))
    print(json.dumps(res)[:2000])


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else str(llm.RUNS / "monitor_scores_all.jsonl"),
         sys.argv[2] if len(sys.argv) > 2 else str(llm.RUNS / "explore.json"))
