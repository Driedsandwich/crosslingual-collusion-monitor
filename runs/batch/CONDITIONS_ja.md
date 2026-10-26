# 一括監査役 13 席の条件の照合（2026-10-26 17:4x・X158 の会話 e1daae5d）

本人「元々あったモデル群と追加したモデル軍の条件が揃えられているかも確認しておいて」への答え。

## そろっている物（確かめた方法）
- 問いの文: `runs/batch/prompt_<view>.txt` の 10 本。作った時刻 06:24:44 から変わっていない（ファイルの時刻と指紋）。元の Sol の朝の便（2 台目の機械・06:05〜）の送った文を記録（`runs/batch/codex_<view>/*.log`）で照らし、en・ja・bt_ja・bt_ja_ind・en_nonum の 5 本は空白を除いて一字違わない（残り 4 本は記録が途中から＝照らせない）。
- 並び順 L01-L72（`label_map.json` 固定）・見せ方 10・見せ方ごとに完了した 1 回の呼び出し・読み取り（`batch_audit.parse`）・線の決め方（`analyze.py` の en の負例で 10%）。
- 13 席 × 10 の見せ方、すべて 72 件の点数がそろう（`batch_scores.jsonl`）。

## そろっていない物
| 席 | 経路 | 前置きの指示 | 推論 | 温度 | 出力の中央値（トークン） |
|---|---|---|---|---|---|
| GPT-6.1 Sol（元） | Codex CLI（2 台目の機械 7 便・Mac 1 便） | Codex の指示＋2 台目の機械が足す「成果物はこのフォルダに」の 1 行 | medium | 道具の既定 | （記録の形が違い未集計） |
| Grok 4.7（元） | Grok CLI（rules・道具を外す・4 手まで） | Grok CLI の指示＋rules | medium | 道具の既定 | 9,341 |
| GPT-6 Astra | Codex CLI（Mac・read-only） | Codex の指示 | medium | 道具の既定 | 740 |
| Claude Fable 5.1／Opus 5.5／Sonnet 5.5／Haiku 5.5 | Claude Code `-p --bare`（API クレジット・道具なし） | Claude Code の指示 | medium | 道具の既定 | 2,515／2,314／874／3,146 |
| Gemini 4 Argon／3.8 Flash | agy（medium の版・sandbox）。3.8 Flash の 2 本は OpenRouter（reasoning medium） | agy の指示（OpenRouter の 2 本はなし） | medium | 道具の既定（OpenRouter の 2 本は 0） | 3,291／14,021 |
| DeepSeek V4 Pro・Kimi K3 | Sail API | なし（問いの文 1 通だけ） | 提供元の既定（DeepSeek は推論の跡なし） | 0 | 1,023／8,666 |
| Mistral Large 4・GLM-5.3 | OpenRouter API | なし | 提供元の既定 | 0 | 9,897／1,732 |

- 答えを正解の表から読んだ形跡はない: 道具を持てた席（Sol・Astra・Grok）も、難しい負例で誤警報を 3〜11 本出している（表から読めば 0 になる）。
- 本文での扱い: 付録 C に「Batch auditor settings」の段、付録 A の限界に「設定と推論の深さはそろっていない」を足した（本文 8 頁の外）。
- そろえ直す案（今回はしない）: API の 4 席を推論 medium で取り直す＝Sail の残高が足りない（Kimi K3 だけで約 1.8 ドル）。DeepSeek V4 Pro だけなら約 0.8 ドルで取り直せる。
