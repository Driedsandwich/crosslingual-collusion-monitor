"""Post hoc (2026-10-26, 17:00 JST): run the added batch auditors over every view, skipping (seat, view) pairs already scored.

Seats: Claude Fable 5.1, Opus 5.5, Sonnet 5.5, Haiku 5.5 (Anthropic API), GPT-6 Astra (Codex), Gemini 4 Argon and
Gemini 3.8 Flash (Antigravity CLI), all at medium effort like the two original batch auditors.
"""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent / "runs"
PY = sys.executable
VIEWS = ["en", "ja", "en_ind", "ja_ind", "ja_idiom", "bt_ja", "bt_ja_ind", "bt_ja_idiom", "en_nonum", "ja_idiom_nonum"]
SEATS = [("claude", "claude-fable-5-1"), ("codex", "gpt-6-astra"), ("agy", "gemini-4-argon-medium"),
         ("claude", "claude-opus-5-5"), ("claude", "claude-sonnet-5-5"), ("agy", "gemini-3.8-flash-medium"),
         ("claude", "claude-haiku-5-5")]


def done():
    f = RUNS / "batch_scores.jsonl"
    rows = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    c = {}
    for r in rows:
        c[(r["monitor"], r["view"])] = c.get((r["monitor"], r["view"]), 0) + 1
    return c


def job(route, model, view):
    argv = [PY, str(HERE / "batch_audit.py"), route, model, view] + (["--effort", "medium"] if route != "agy" else [])
    r = subprocess.run(argv, capture_output=True, text=True, env={**__import__("os").environ, "PYTHONPATH": str(HERE)})
    line = (r.stdout.strip().splitlines() or [""])[-1]
    print(f"{route} {model} {view} rc={r.returncode} :: {line[:160]} {r.stderr.strip()[-200:]}", flush=True)


if __name__ == "__main__":
    have = done()
    todo = [(r, m, v) for v in VIEWS for r, m in SEATS if have.get(("batch:" + m, v), 0) < 72]
    print("todo", len(todo), flush=True)
    with ThreadPoolExecutor(max_workers=int(sys.argv[1]) if len(sys.argv) > 1 else 8) as ex:
        list(ex.map(lambda t: job(*t), todo))
    print("finished", flush=True)
