"""Meaning-preservation audit packets (PROTOCOL.md): all 24 `collude` transcripts plus 6 `benign` and 6 `hardneg` drawn with a
fixed seed. Transcripts get neutral labels P01-P36 (shuffled) so the reader does not see the class; the map stays local.

Written during the sprint (2026-10-26).
  python audit_packets.py build [--parts 3]   write runs/audit/packet_<k>.md and runs/audit/packet_map.json
  python audit_packets.py collect             merge runs/audit/result_<k>.json into runs/audit/verdicts.json and
                                              write runs/audit/exclude_ids.txt (transcripts with any DROP or ADD)
"""
import argparse
import json
import random
from pathlib import Path

import llm

AUD = llm.RUNS / "audit"
AUD.mkdir(exist_ok=True)
CHECK = ["ja", "en_ind", "ja_ind", "ja_idiom"]


def build(parts):
    ts = {json.loads(l)["id"]: json.loads(l) for l in (llm.RUNS / "transcripts_all.jsonl").read_text().splitlines() if l.strip()}
    rng = random.Random(4242)
    col = sorted(i for i, t in ts.items() if t["class"] == "collude")
    ben = sorted(i for i, t in ts.items() if t["class"] == "benign")
    har = sorted(i for i, t in ts.items() if t["class"] == "hardneg")
    chosen = col + rng.sample(ben, 6) + rng.sample(har, 6)
    rng.shuffle(chosen)
    label = {i: f"P{k + 1:02d}" for k, i in enumerate(chosen)}
    (AUD / "packet_map.json").write_text(json.dumps(label, indent=1))
    per = -(-len(chosen) // parts)
    for k in range(parts):
        out = []
        for i in chosen[k * per:(k + 1) * per]:
            t = ts[i]
            en = [m["text"] for h in t["rounds"] for m in h["msgs"]]
            sp = [m["speaker"] for h in t["rounds"] for m in h["msgs"]]
            out.append(f"## {label[i]}\n")
            for j in range(len(en)):
                out.append(f"### message {j + 1} ({sp[j]})")
                out.append(f"- en: {en[j]}")
                for v in CHECK:
                    out.append(f"- {v}: {t['views'][v][j]}")
                out.append("")
        (AUD / f"packet_{k + 1}.md").write_text("\n".join(out))
        print(f"packet_{k + 1}.md", len(chosen[k * per:(k + 1) * per]), "transcripts")


def collect():
    inv = {lab: i for i, lab in json.loads((AUD / "packet_map.json").read_text()).items()}
    verdicts, bad = {}, set()
    for f in sorted(AUD.glob("result_*.json")):
        for e in json.loads(f.read_text()):
            i = inv[e["transcript"]]
            verdicts.setdefault(i, {})[e["variant"]] = {"verdict": e["verdict"], "note": e.get("note", "")}
            if e["verdict"] in ("DROP", "ADD"):
                bad.add(i)
    missing = [(lab, v) for lab, i in inv.items() for v in CHECK if v not in verdicts.get(i, {})]
    (AUD / "verdicts.json").write_text(json.dumps(verdicts, indent=1, ensure_ascii=False))
    (AUD / "exclude_ids.txt").write_text("\n".join(sorted(bad)) + "\n")
    print("transcripts", len(verdicts), "missing pairs", len(missing), missing[:5], "excluded", sorted(bad))



# Round 2 (exploratory, see PROTOCOL.md): the 18 hard negatives not audited in round 1 (all six rewrites) and the 36
# round-1 transcripts (the two number-free rewrites only). Fresh neutral labels Q01-Q54; map in runs/audit/packet2_map.json.
CHECK2 = ["ja", "en_ind", "ja_ind", "ja_idiom", "en_nonum", "ja_idiom_nonum"]


def build2(parts=4):
    ts = {json.loads(l)["id"]: json.loads(l) for l in (llm.RUNS / "transcripts_all.jsonl").read_text().splitlines() if l.strip()}
    done1 = set(json.loads((AUD / "packet_map.json").read_text()))
    new_hard = sorted(i for i, t in ts.items() if t["class"] == "hardneg" and i not in done1)
    plan = {i: CHECK2 for i in new_hard}
    plan.update({i: ["en_nonum", "ja_idiom_nonum"] for i in sorted(done1)})
    chosen = sorted(plan)
    rng = random.Random(4343)
    rng.shuffle(chosen)
    label = {i: f"Q{k + 1:02d}" for k, i in enumerate(chosen)}
    (AUD / "packet2_map.json").write_text(json.dumps({"label": label, "plan": plan}, indent=1))
    per = -(-len(chosen) // parts)
    for k in range(parts):
        out = []
        for i in chosen[k * per:(k + 1) * per]:
            t = ts[i]
            en = [m["text"] for h in t["rounds"] for m in h["msgs"]]
            sp = [m["speaker"] for h in t["rounds"] for m in h["msgs"]]
            out.append(f"## {label[i]}  (rewrites to judge: {', '.join(plan[i])})\n")
            for j in range(len(en)):
                out.append(f"### message {j + 1} ({sp[j]})")
                out.append(f"- en: {en[j]}")
                for v in plan[i]:
                    out.append(f"- {v}: {t['views'][v][j]}")
                out.append("")
        (AUD / f"packet2_{k + 1}.md").write_text("\n".join(out))
        print(f"packet2_{k + 1}.md", len(chosen[k * per:(k + 1) * per]), "transcripts")


def collect2():
    m = json.loads((AUD / "packet2_map.json").read_text())
    inv = {lab: i for i, lab in m["label"].items()}
    verdicts, bad_primary, bad_nonum = {}, set(), set()
    for f in sorted(AUD.glob("result2_*.json")):
        for e in json.loads(f.read_text()):
            i = inv[e["transcript"]]
            verdicts.setdefault(i, {})[e["variant"]] = {"verdict": e["verdict"], "note": e.get("note", "")}
            if e["verdict"] in ("DROP", "ADD"):
                (bad_nonum if e["variant"].endswith("_nonum") else bad_primary).add(i)
    missing = [(m["label"][i], v) for i, vs in m["plan"].items() for v in vs if v not in verdicts.get(i, {})]
    (AUD / "verdicts2.json").write_text(json.dumps(verdicts, indent=1, ensure_ascii=False))
    prev = set((AUD / "exclude_ids.txt").read_text().split())
    (AUD / "exclude_ids.txt").write_text("\n".join(sorted(prev | bad_primary)) + "\n")
    (AUD / "exclude_ids_nonum.txt").write_text("\n".join(sorted(bad_nonum)) + "\n")
    print("transcripts", len(verdicts), "missing pairs", len(missing), missing[:5],
          "excluded primary", sorted(bad_primary), "excluded nonum", sorted(bad_nonum))



if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--parts", type=int, default=3)
    a = ap.parse_args()
    {"build": lambda: build(a.parts), "collect": collect, "build2": lambda: build2(4), "collect2": collect2}[a.cmd]()
