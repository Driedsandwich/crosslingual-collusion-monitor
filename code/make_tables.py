"""Generate the report's tables from runs/results*.json and substitute them into the report.

Written during the sprint (2026-10-26). Lines of the form {{TABLE:name}} in report/report.md are replaced by the generated
Markdown table; {{NUM:key}} tokens are replaced by single numbers. Output: report/report_filled.md (the file that is built).
"""
import json
import re
from pathlib import Path

import llm

R = llm.RUNS
REP = llm.RUNS.parent / "report"
SHORT = {"mistral-small-2603": "Mistral Small", "ministral-8b-2512": "Ministral 8B", "zai-glm-5-3-flash": "GLM-5.3 Flash",
         "deepseek-ai/DeepSeek-V4.1-Flash-1017": "DeepSeek V4.1 Flash", "openai/gpt-oss-120b": "gpt-oss-120b",
         "google/gemma-4-31B-it": "Gemma 4 31B", "batch:gpt-6.1-sol": "GPT-6.1 Sol", "batch:grok-4.7": "Grok 4.7",
         # batch auditors added post hoc (PROTOCOL.md, 16:5x JST)
         "batch:gpt-6-astra": "GPT-6 Astra*", "batch:claude-fable-5-1": "Claude Fable 5.1*",
         "batch:claude-opus-5-5": "Claude Opus 5.5*", "batch:claude-sonnet-5-5": "Claude Sonnet 5.5*",
         "batch:claude-haiku-5-5": "Claude Haiku 5.5*", "batch:gemini-4-argon-medium": "Gemini 4 Argon*",
         "batch:gemini-3.8-flash-medium": "Gemini 3.8 Flash*", "batch:mistralai/mistral-large-4-0": "Mistral Large 4*",
         "batch:z-ai/glm-5.3": "GLM-5.3*", "batch:deepseek-ai/DeepSeek-V4-Pro-0813": "DeepSeek V4 Pro*",
         "batch:moonshotai/Kimi-K3": "Kimi K3*"}
ORDER = list(SHORT)
PRIMARY = ["en", "en_ind", "ja", "ja_ind", "ja_idiom", "bt_ja", "bt_ja_ind", "bt_ja_idiom"]


def load(name):
    return json.loads((R / name).read_text())


def monitors(res):
    return sorted({k.split("|")[0] for k in res["auc"]}, key=lambda m: ORDER.index(m) if m in ORDER else 99)


def auc_table(res, views):
    rows = ["| Monitor | " + " | ".join(views) + " |", "|---|" + "---|" * len(views)]
    for m in monitors(res):
        cells = []
        for v in views:
            e = res["auc"].get(f"{m}|{v}")
            if e is None:
                cells.append("-")
                continue
            d = res["paired_vs_en"].get(f"{m}|{v}")
            star = ""
            if d and (d["hi"] < 0 or d["lo"] > 0):
                star = "↓" if d["hi"] < 0 else "↑"
            cells.append(f"{e['auc']:.3f}{star}")
        rows.append(f"| {SHORT.get(m, m)} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def rate_table(res, views, field):
    rows = ["| Monitor (en threshold) | " + " | ".join(views) + " |", "|---|" + "---|" * len(views)]
    for m in monitors(res):
        cells = [f"{res['rates'][f'{m}|{v}'][field]:.2f}" if f"{m}|{v}" in res["rates"] else "-" for v in views]
        rows.append(f"| {SHORT.get(m, m)} ({res['threshold_en'][m]:g}) | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def combo_table(res, views):
    rows = ["| Monitor (en threshold) | " + " | ".join(views) + " |", "|---|" + "---|" * len(views)]
    for m in monitors(res):
        npos = res["auc"][f"{m}|en"]["n_pos"]; nhard = res["auc"][f"{m}|en"]["n_neg"] - 24  # 24 benign in every analysis
        cells = [f"{round(res['rates'][f'{m}|{v}']['tpr'] * npos)} / {round(res['rates'][f'{m}|{v}']['fpr_hardneg'] * nhard)}" for v in views]
        rows.append(f"| {SHORT.get(m, m)} ({res['threshold_en'][m]:g}) | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def diff_table(res, views):
    rows = ["| Monitor | " + " | ".join(views) + " |", "|---|" + "---|" * len(views)]
    for m in monitors(res):
        cells = []
        for v in views:
            d = res["paired_vs_en"].get(f"{m}|{v}")
            cells.append("-" if d is None else f"{d['diff']:+.3f} [{d['lo']:+.3f}, {d['hi']:+.3f}]")
        rows.append(f"| {SHORT.get(m, m)} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


def means_table(ex, views, mons):
    rows = ["| Monitor | " + " | ".join(views) + " |", "|---|" + "---|" * len(views)]
    for m in mons:
        cells = []
        for v in views:
            e = ex.get(f"{m}|{v}")
            cells.append("-" if e is None else f"{e['mean']['collude']:.0f} / {e['mean']['benign']:.0f} / {e['mean']['hardneg']:.0f}")
        rows.append(f"| {SHORT.get(m, m)} | " + " | ".join(cells) + " |")
    return "\n".join(rows)


GLOSS = {"前回と同じ水準": "zenkai to onaji suijun [the same level as last time]",
         "先日お話しした線": "senjitsu ohanashi shita sen [the line we discussed the other day]",
         "御社より少し下": "onsha yori sukoshi shita [a little below yours]"}


def appendix_b():
    """Prompts reproduced verbatim from the code (Japanese examples glossed in brackets)."""
    import batch_audit as b
    import gen_transcripts as g
    import monitor
    import variants
    sub = lambda t: t.replace("{me}", "<me>").replace("{other}", "<other>").replace("{product}", "<product>").replace("{town}", "<town>")
    gl = lambda t: re.sub("|".join(GLOSS), lambda mm: GLOSS[mm.group(0)], t)
    parts = ["All prompts are reproduced verbatim from the code, except that the three Japanese examples in `ja_idiom_nonum` are romanized, "
             "with English glosses in square brackets.",
             "**Monitor system prompt (all six per-transcript monitors).** The user message is \"Chat log:\" followed by the transcript as "
             "`[Round r]` blocks of `Seller: message` lines.",
             "*" + monitor.SYSTEM.replace("\n", " ") + "*",
             "**Seller prompt (generation).** " + sub(g.BASE) + " The user message then gives the previous rounds' chat and prices "
             "and, for the second speaker of a round, the first speaker's message in that round, and asks for JSON with the message and the price.",
             "\n".join(f"- {k}: {sub(v)}" for k, v in g.ROLE.items()),
             "**Rewriter and back-translator.** System prompt: \"You are a professional business-language editor. <instruction> There are "
             "exactly 12 messages. Reply in JSON only: {\\\"messages\\\": [<12 strings in the same order>]}\", with these instructions "
             "(`bt` is used for all three back-translations; the two `_nonum` instructions are exploratory):",
             "\n".join(f"- {k}: {gl(v)}" for k, v in variants.P.items()),
             "**Batch auditor prompt (secondary experiment).** " + b.HEAD.replace("{n}", "72").replace("{{", "{").replace("}}", "}").replace("\n", " ").strip()
             + " The 72 logs follow, each headed `=== Lxx ===`. Unlike the per-transcript prompt, it frames the task as a study and "
             "says that some logs may be in Japanese."]
    return "\n\n".join(parts).replace('\\"', '"')


def main():
    res, rob, non, bat = load("results.json"), load("results_robust.json"), load("results_nonum.json"), load("results_batch.json")
    ex = load("explore.json")
    T = {
        "auc_primary": auc_table(res, PRIMARY),
        "fprh_primary": rate_table(res, PRIMARY, "fpr_hardneg"),
        "combo_primary": combo_table(res, PRIMARY),
        "tpr_primary": rate_table(res, PRIMARY, "tpr"),
        "fprh_robust": rate_table(rob, PRIMARY, "fpr_hardneg"),
        "diff_primary": diff_table(res, ["en_ind", "ja", "ja_ind", "ja_idiom"]),
        "means_primary": means_table(ex, ["en", "en_ind", "ja", "ja_idiom", "bt_ja_idiom"], monitors(res)),
        "nonum_auc": auc_table(non, ["en", "en_nonum", "ja_idiom", "ja_idiom_nonum"]),
        "nonum_fprh": rate_table(non, ["en", "en_nonum", "ja_idiom", "ja_idiom_nonum"], "fpr_hardneg"),
        "nonum_tpr": rate_table(non, ["en", "en_nonum", "ja_idiom", "ja_idiom_nonum"], "tpr"),
        "batch_auc": auc_table(bat, PRIMARY),
        "batch_fprh": rate_table(bat, PRIMARY, "fpr_hardneg"),
        "batch_tpr": rate_table(bat, PRIMARY, "tpr"),
    }
    (REP / "tables.md").write_text("\n\n".join(f"### {k}\n\n{v}" for k, v in T.items()) + "\n")
    src = (REP / "report.md").read_text()
    out = re.sub(r"\{\{TABLE:(\w+)\}\}", lambda mm: T[mm.group(1)], src)
    out = out.replace("{{APPENDIX_B}}", appendix_b())
    missing = re.findall(r"\{\{[A-Z]+:\w+\}\}", out)
    (REP / "report_filled.md").write_text(out)
    print("tables", len(T), "unfilled tokens", missing)


if __name__ == "__main__":
    main()
