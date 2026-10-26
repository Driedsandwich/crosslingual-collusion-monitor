"""Post hoc (2026-10-26, 17:3x JST): re-run the calls that were missing from the added batch auditors.
Mistral Large 4 on OpenRouter again (the earlier calls hung for 900 s; now two at a time with a 300 s timeout), and the two
Gemini 3.8 Flash views that returned empty answers twice through the Antigravity CLI, re-routed to the same model on
OpenRouter at medium reasoning and filed under the same seat."""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
HERE = Path(__file__).resolve().parent
RUNS = HERE.parent / "runs"
have = {}
for l in (RUNS / "batch_scores.jsonl").read_text().splitlines():
    r = json.loads(l); have[(r["monitor"], r["view"])] = have.get((r["monitor"], r["view"]), 0) + 1
JOBS = [["mistralai/mistral-large-4-0", v] for v in ["ja", "ja_idiom", "bt_ja_ind", "bt_ja_idiom", "en_nonum", "ja_idiom_nonum"]]
JOBS += [["google/gemini-3.8-flash", v, "gemini-3.8-flash-medium", "--effort", "medium"] for v in ["ja_ind", "ja_idiom_nonum"]]
JOBS = [j for j in JOBS if have.get(("batch:" + (j[2] if len(j) > 2 else j[0]), j[1]), 0) < 72]
env = {**os.environ, "PYTHONPATH": str(HERE), "X158_BUDGET_OR": "3.0"}
def job(j):
    r = subprocess.run([sys.executable, str(HERE / "batch_audit.py"), "api"] + j, capture_output=True, text=True, env=env)
    print(" ".join(j[:2]), f"rc={r.returncode} ::", (r.stdout.strip().splitlines() or [""])[-1][:160], r.stderr.strip()[-200:], flush=True)
print("todo", len(JOBS), flush=True)
with ThreadPoolExecutor(max_workers=2) as ex:
    list(ex.map(job, JOBS))
print("finished", flush=True)
