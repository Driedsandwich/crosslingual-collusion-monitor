"""Minimal chat client (Mistral API and Sail Research API) with a call ledger and per-route budget stops.

Written during the sprint (2026-10-26). Every call is appended to ledger.jsonl
(model, purpose, tokens, latency, status). API keys are read from the macOS
keychain items `mistral-api` / `sail-api` and are never printed or written.
"""
import json
import os
import subprocess
import threading
import time
from pathlib import Path

import httpx

ROUTES = {
    "mistral": {"api": "https://api.mistral.ai/v1/chat/completions", "keychain": "mistral-api",
                "budget": float(os.environ.get("X158_BUDGET_USD", "3.0"))},
    "sail": {"api": "https://api.sailresearch.com/v1/chat/completions", "keychain": "sail-api",
             "budget": float(os.environ.get("X158_BUDGET_SAIL", "1.5"))},
    # post hoc batch auditors only (2026-10-26 17:0x JST, author's approval): Mistral route returned HTTP 402
    "openrouter": {"api": "https://openrouter.ai/api/v1/chat/completions", "keychain": "openrouter-api",
                   "budget": float(os.environ.get("X158_BUDGET_OR", "3.0"))},
}
OPENROUTER_MODELS = {"mistralai/mistral-large-4-0", "z-ai/glm-5.3", "google/gemini-3.8-flash"}
SAIL_MODELS = {"deepseek-ai/DeepSeek-V4.1-Flash-1017", "openai/gpt-oss-120b", "google/gemma-4-31B-it",
               "moonshotai/Kimi-K3", "deepseek-ai/DeepSeek-V4-Pro-0813"}  # last two: post hoc batch auditors
HERE = Path(__file__).resolve().parent
RUNS = HERE.parent / "runs"
RUNS.mkdir(exist_ok=True)
LEDGER = RUNS / "ledger.jsonl"

# USD per 1M tokens (input, output), list prices read from docs.mistral.ai model pages on
# 2026-10-26. Used for the budget stop; the report states measured token counts, not invoices.
PRICE = {
    "mistral-small-2603": (0.15, 0.60),
    "mistral-large-2512": (0.50, 1.50),
    "zai-glm-5-3-flash": (0.15, 0.50),
    "ministral-8b-2512": (0.15, 0.15),
    # Sail Research, Default (ASAP) window, docs.sailresearch.com/pricing read on 2026-10-26 05:4x JST
    "deepseek-ai/DeepSeek-V4.1-Flash-1017": (0.09, 0.30),
    "openai/gpt-oss-120b": (0.06, 0.40),
    "google/gemma-4-31B-it": (0.40, 0.60),
    # post hoc batch auditors (2026-10-26 17:2x): Sail pricing page read 17:2x JST; zai-glm-5-3 from the audit tool's table
    "moonshotai/Kimi-K3": (1.50, 10.00),
    "deepseek-ai/DeepSeek-V4-Pro-0813": (0.92, 2.77),
    "zai-glm-5-3": (1.40, 4.40),
    # OpenRouter public model list read 16:4x JST
    "mistralai/mistral-large-4-0": (1.36, 4.18),
    "z-ai/glm-5.3": (0.07, 1.40),
    "google/gemini-3.8-flash": (0.825, 4.125),
}
BUDGET_USD = ROUTES["mistral"]["budget"]  # kept for older callers

_lock = threading.Lock()
_keys = {}


def route_of(model):
    return "sail" if model in SAIL_MODELS else ("openrouter" if model in OPENROUTER_MODELS else "mistral")


def _api_key(route):
    if route not in _keys:
        _keys[route] = subprocess.run(["security", "find-generic-password", "-s", ROUTES[route]["keychain"], "-w"],
                                      capture_output=True, text=True, check=True).stdout.strip()
    return _keys[route]


def spent_usd(route=None):
    """Upper-bound spend from the ledger (list prices x measured tokens), optionally for one route."""
    if not LEDGER.exists():
        return 0.0
    total = 0.0
    for line in LEDGER.read_text().splitlines():
        r = json.loads(line)
        m = r.get("req_model", r["model"])
        if route is not None and route_of(m) != route:
            continue
        pin, pout = PRICE.get(m, PRICE.get(r["model"], (2.0, 6.0)))
        total += r.get("in", 0) * pin / 1e6 + r.get("out", 0) * pout / 1e6
    return total


class BudgetExceeded(RuntimeError):
    pass


def chat(model, messages, purpose, temperature=0.0, max_tokens=800, json_mode=False, seed=None, retries=6,
         reasoning_effort=None, timeout=180):
    """One chat completion. Returns (text, usage). Raises BudgetExceeded before sending if over the route budget."""
    route = route_of(model)
    if spent_usd(route) > ROUTES[route]["budget"]:
        raise BudgetExceeded(f"{route} budget {ROUTES[route]['budget']} USD reached")
    API = ROUTES[route]["api"]
    body = {"model": model, "messages": messages, "temperature": temperature, "max_tokens": max_tokens}
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    if seed is not None and route == "mistral":  # Sail rejects `seed` (HTTP 400 unsupported_feature, 2026-10-26)
        body["random_seed"] = seed
    if reasoning_effort is not None:
        if route == "openrouter":  # OpenRouter's unified reasoning setting
            body["reasoning"] = {"effort": reasoning_effort}
        else:
            body["reasoning_effort"] = reasoning_effort
    headers = {"Authorization": f"Bearer {_api_key(route)}", "Content-Type": "application/json"}
    delay = 2.0
    for attempt in range(retries):
        t0 = time.time()
        try:
            r = httpx.post(API, json=body, headers=headers, timeout=timeout)
        except httpx.HTTPError as e:
            status, err = -1, type(e).__name__
        else:
            status, err = r.status_code, None
            if status == 200:
                d = r.json()
                u = d.get("usage", {})
                text = d["choices"][0]["message"]["content"]
                if isinstance(text, list):  # thinking models return parts
                    text = "".join(p.get("text", "") for p in text if p.get("type") == "text")
                rec = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": d.get("model", model), "req_model": model,
                       "purpose": purpose, "in": u.get("prompt_tokens", 0), "out": u.get("completion_tokens", 0),
                       "sec": round(time.time() - t0, 2), "status": 200, "attempt": attempt}
                with _lock:
                    with LEDGER.open("a") as f:
                        f.write(json.dumps(rec) + "\n")
                return text, u
        with _lock:
            with LEDGER.open("a") as f:
                f.write(json.dumps({"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": model, "req_model": model,
                                    "purpose": purpose, "in": 0, "out": 0, "status": status, "err": err,
                                    "attempt": attempt}) + "\n")
        if status in (400, 401, 403, 404, 422):
            raise RuntimeError(f"HTTP {status} for {model}: {r.text[:300]}")
        time.sleep(delay)
        delay = min(delay * 2, 60)
    raise RuntimeError(f"gave up after {retries} attempts ({model}, {purpose})")


def parse_json(text):
    """Parse the first JSON object in a model reply."""
    s = text.strip()
    if s.startswith("```"):
        s = s.strip("`")
        s = s[s.find("{"):]
    i, j = s.find("{"), s.rfind("}")
    return json.loads(s[i:j + 1])
