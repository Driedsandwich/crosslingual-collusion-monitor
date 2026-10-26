"""Post hoc (2026-10-26, 17:3x JST, approved by the author): flagship models of four more developers as batch auditors
through the Sail API, and Mistral Large 4 and GLM-5.3 through OpenRouter after the Mistral route returned HTTP 402
(route budgets: Sail 4.0, OpenRouter 3.0 USD for this run)."""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
HERE = Path(__file__).resolve().parent
RUNS = HERE.parent / "runs"
VIEWS = ["en", "ja", "en_ind", "ja_ind", "ja_idiom", "bt_ja", "bt_ja_ind", "bt_ja_idiom", "en_nonum", "ja_idiom_nonum"]
SEATS = sys.argv[1].split(",") if len(sys.argv) > 1 else ["deepseek-ai/DeepSeek-V4-Pro-0813", "moonshotai/Kimi-K3"]
have = {}
for l in (RUNS / "batch_scores.jsonl").read_text().splitlines():
    r = json.loads(l); have[(r["monitor"], r["view"])] = have.get((r["monitor"], r["view"]), 0) + 1
todo = [(m, v) for v in VIEWS for m in SEATS if have.get(("batch:" + m, v), 0) < 72]
env = {**os.environ, "PYTHONPATH": str(HERE), "X158_BUDGET_USD": "4.5", "X158_BUDGET_SAIL": "4.0", "X158_BUDGET_OR": "3.0"}
def job(t):
    m, v = t
    r = subprocess.run([sys.executable, str(HERE / "batch_audit.py"), "api", m, v], capture_output=True, text=True, env=env)
    print(f"api {m} {v} rc={r.returncode} :: {(r.stdout.strip().splitlines() or [''])[-1][:160]} {r.stderr.strip()[-200:]}", flush=True)
print("todo", len(todo), flush=True)
with ThreadPoolExecutor(max_workers=6) as ex:
    list(ex.map(job, todo))
print("finished", flush=True)
