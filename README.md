# Cross-lingual collusion monitoring

Code, prompts, synthetic transcripts and scores for the report *Euphemistic Register Breaks Budget-Set English Thresholds of LLM Collusion Monitors, Even Where Rankings Hold* (AI Collusion Research Sprint, Apart Research, October 2026).

The question: does an LLM collusion monitor whose prompt and threshold are fixed on English logs still separate collusion from competition when the same seller chats are written in Japanese, in indirect euphemistic English, or in Japanese business register, and does translating back to English help? Short answer: the strongest monitors keep ranking collusion almost perfectly, but thresholds set for a false-alarm budget on English negatives fail under indirect register (more false alarms for strong monitors, misses for weak ones), and back-translation does not repair it. Post hoc, thresholds placed midway between the English classes, or re-fixed on held-out deployment-view data, restore the strong monitors but only partly the weak ones.

## Prior work

**No preexisting code.** Everything in this repository was written during the sprint (25 October 2026, Anywhere on Earth). The sprint's starter repositories were downloaded for reference, but no code from them is used.

## Layout

| Path | What it is |
|---|---|
| `code/PROTOCOL.md` | Analysis plan, frozen before any scored monitor output was inspected; deviations at the end |
| `code/llm.py` | Minimal chat client (Mistral API, Sail Research API) with a call ledger and per-route budget stops |
| `code/gen_transcripts.py` | Two-seller repeated pricing market; 24 markets each of `collude`, `benign`, `hardneg` |
| `code/variants.py` | Content-matched rewrites: `ja`, `en_ind`, `ja_ind`, `ja_idiom`, and back-translations `bt_*` |
| `code/monitor.py` | Six per-transcript monitors, one transcript per call |
| `code/explore.py`, `code/make_tables.py` | Exploratory class means and per-class AUC; report tables |
| `code/batch_audit.py` | Secondary experiment: batch auditors, one call per view (GPT-6.1 Sol and Grok 4.7 pre-registered; Claude, GPT-6 Astra, Gemini, Mistral Large 4, GLM-5.3, DeepSeek V4 Pro and Kimi K3 added post hoc) |
| `code/run_more_auditors.py`, `code/run_more_api.py` | Runners for the eleven post hoc batch auditors |
| `code/run_detour.py` | Re-runs of the stalled or empty batch calls (Mistral Large 4, Gemini 3.8 Flash) |
| `code/recalibrate.py` | Post hoc: thresholds re-fixed on each view's negatives, the English midpoint threshold, and AUC against hard negatives only (Appendix D, Tables 6-8) |
| `code/audit_packets.py` | Meaning-preservation audit packets (neutral labels) and the merge of verdicts |
| `code/analyze.py`, `code/fig.py` | AUC with stratified bootstrap, paired differences, thresholded rates, figures |
| `code/build_report.py` | Fills the official sprint template (.docx) from Markdown and exports PDF |
| `runs/transcripts_en.jsonl`, `runs/transcripts_all.jsonl` | Generated transcripts with prices, and all eight views |
| `runs/monitor_scores*.jsonl`, `runs/batch_scores.jsonl` | Raw scores |
| `runs/results.json`, `runs/results_batch.json` | Analysis output |
| `runs/audit/` | Audit instructions, packets, verdicts |
| `runs/ledger.jsonl` | One line per API call: model, purpose, token counts, latency, status |
| `report/` | Report source and PDF |

## Reproduce

Python 3 with `numpy`, `matplotlib`, `httpx`, `python-docx`. API keys are read from the macOS keychain items `mistral-api` and `sail-api` (edit `llm.py` for another store).

```
python code/gen_transcripts.py
python code/variants.py                                         # the seven primary views
python code/variants.py --views en_nonum,ja_idiom_nonum         # exploratory number-free views
python code/monitor.py                                          # writes runs/monitor_scores.jsonl
python code/monitor.py --views en_nonum,ja_idiom_nonum --out runs/monitor_scores_nonum.jsonl
python code/batch_audit.py build                                # batch prompts; the batch calls need the Codex, Grok, Claude Code and Antigravity CLIs
python code/run_more_auditors.py && python code/run_more_api.py  # post hoc batch auditors (API keys from the macOS keychain)
PY=python zsh code/run_analysis.sh                              # all analyses and the figure
python code/make_tables.py                                      # tables into report/report_filled.md
```

The primary scores were written in three files (`monitor_scores.jsonl`, `monitor_scores_idiom.jsonl`, `monitor_scores_bt.jsonl`) because the views were scored as they became ready; `run_analysis.sh` merges them.

Total API spend for the full run was about 1.8 USD (measured on the providers' usage pages).

## Licence

Code: MIT. Transcripts, scores and report: CC BY 4.0. All markets, firms and towns are fictional.
