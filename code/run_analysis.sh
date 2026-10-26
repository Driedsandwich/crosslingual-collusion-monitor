#!/bin/zsh
# Merge score files and run every analysis reported in the paper. Written during the sprint (2026-10-26).
#   results.json            primary, pre-specified, all 72 transcripts
#   results_excl.json       primary, without transcripts that failed the meaning-preservation audit (PROTOCOL)
#   results_robust.json     exploratory: also without hard negatives whose English original reads as coordination
#   results_nonum.json      exploratory number-free views (with their audit and label-noise exclusions)
#   results_batch*.json     secondary experiment (batch auditors), all and robust
H=${0:A:h}; R=$H/../runs; A=$R/audit; PY=${PY:-python3}
cat $R/monitor_scores.jsonl $R/monitor_scores_idiom.jsonl $R/monitor_scores_bt.jsonl > $R/monitor_scores_primary.jsonl
cat $R/monitor_scores_primary.jsonl $R/monitor_scores_nonum.jsonl > $R/monitor_scores_all.jsonl
cat $A/exclude_ids_nonum.txt $A/exclude_robust_ids.txt | sort -u > $A/exclude_nonum_all.txt
$PY $H/analyze.py --scores $R/monitor_scores_primary.jsonl --out $R/results.json > /dev/null
$PY $H/analyze.py --scores $R/monitor_scores_primary.jsonl --exclude $A/exclude_ids.txt --out $R/results_excl.json > /dev/null
$PY $H/analyze.py --scores $R/monitor_scores_primary.jsonl --exclude $A/exclude_robust_ids.txt --out $R/results_robust.json > /dev/null
$PY $H/analyze.py --scores $R/monitor_scores_all.jsonl --exclude $A/exclude_nonum_all.txt --out $R/results_nonum.json > /dev/null
$PY $H/analyze.py --scores $R/batch_scores.jsonl --out $R/results_batch.json > /dev/null
$PY $H/analyze.py --scores $R/batch_scores.jsonl --exclude $A/exclude_nonum_all.txt --out $R/results_batch_robust.json > /dev/null
$PY $H/explore.py $R/monitor_scores_all.jsonl $R/explore.json > /dev/null
$PY $H/explore.py $R/batch_scores.jsonl $R/explore_batch.json > /dev/null
mkdir -p $H/../report
$PY $H/fig.py $R/results.json $H/../report/fig_main.png
# fig_batch.png (two auditors only) was dropped when eleven batch auditors were added post hoc; Table 5 reports them
wc -l $R/monitor_scores_all.jsonl $R/batch_scores.jsonl
