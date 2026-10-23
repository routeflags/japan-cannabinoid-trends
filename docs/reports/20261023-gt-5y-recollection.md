# 5年系列の再取得（THC・CBG・HHC・THCV）— 2026-10-23

**種別:** 報告書（issue ではない）
**対象:** `datasets/cannabinoid-raw-collection`（Google Trends 5年系列）
**契機:** `ISS-20261015-GT-003`（`docs/issues/closed/resolved/20261015_p1_unreproducible-gt-5y-averages.md`）の残作業
**実施:** 2026-10-23（UTC）、owner の依頼「とれてない google トレンドを取得」にもとづく

---

## 1. 何が欠けていたか

5年系列（`today 5-y`）は 13 化合物のうち 9 化合物が週次 raw を持っていたが、
THC・CBG・HHC・THCV の 4 化合物は **summary-only** だった:

- 出所は `data/raw/google_trends/20261008T093228Z-google-trends-5y-baseline/` の
  summary JSON（`thc_5y_summary.json` 等）。週次系列を収蔵していない。
- そのため `docs/audits/gt-summary.json` はこの 4 件を `shape=baseline`（261 週）として
  **記録値をそのまま通し**、`data_period` / `raw_timeline` を `unavailable` にしていた。
- publication ページの 5年ブロックも「収集期間」を書けない状態だった。

## 2. 手順

1. **窓の登録**: 2026-10-23 の `today 5-y` は `2021-10-23 .. 2026-10-23` に解決される。
   ⚠️ 登録済みの `2021-10-10_2026-10-12` は許容誤差（7 日）を外れるため、
   `compile-window` が `no_registered_timeframe_matches` で拒否した（P6 = 期間の無断切替なし）。
   → 週グリッドに合わせた新窓 [`metadata/windows/2021-10-17_2026-10-18.json`](../../metadata/windows/2021-10-17_2026-10-18.json)
   を登録。両端が日曜 UTC 0 時で、`today 5-y` の解決結果と各 6 日 / 5 日の差（誤差内）。
2. **計画書**: `datasets/cannabinoid-raw-collection/metadata/plans/gt-5y-recollect-{thc,cbg,hhc,thcv}.json`
   （既存の CBD 計画書と同じ形。`query_id` は `metadata/queries/query-registry.json` の
   `{thc,cbg,hhc,thcv}-general-ja`）。
3. **収集**: `scripts/collection/google-trends-live-guard.py fetch`
   （= `collect --live`、時間制限 300s、ログは `.staging/tooling_logs/`）を 1 化合物 1 run で 4 回。
   前に `probe`（MCP の `initialize` + `tools/list` のみ）で到達性を確認した。
4. **L1**: 4 run すべて `validation.cli gate-run` = PASS → catalog 採用
   （`data/raw/google_trends/<run-id>/`）。quarantine なし。

## 3. 収集結果（2026-10-23、geo=JP / today 5-y）

| 化合物 | run_id | 週数 | 平均 | ピーク | 最新値 | ゼロ週 |
|---|---|---:|---:|---|---:|---:|
| THC | `20261023T162500Z-google-trends-thc-5y` | 262 | 12.4084 | 2025-08-31（100） | 7 | 0 |
| CBG | `20261023T160420Z-google-trends-cbg-5y` | 262 | 48.1756 | 2026-05-24（100） | 36 | 11 |
| HHC | `20261023T160428Z-google-trends-hhc-5y` | 262 | 2.4924 | 2022-03-06（100） | 0 | 72 |
| THCV | `20261023T160436Z-google-trends-thcv-5y` | 262 | 7.4313 | 2023-09-03（100） | 0 | 217 |

- 4 run の観測範囲はすべて `2021-10-17 〜 2026-10-18`（登録窓と一致）。
- 各 run は verbatim な MCP 応答（`payload.json`、text 表）と解析済み系列（`records_<term>.json`）を持つ。
- 数値の正本は `docs/audits/gt-summary.json`（`processing.cli gt-summary` の生成物）。

## 4. 下流への影響

- `docs/audits/gt-summary.json`: `by_shape` が `{baseline: 4, series: 10}` → `{series: 14}`。
  `unavailable_mean` は空のまま。4 化合物の `stats` は raw 系列からの算出値になった。
- `publication/{research_thc,research_cbg,research_hhc,research_thcv}.html`: 5年ブロックを
  `gt-summary --write` で再生成（収集期間が入り、出所が新 run を指す）。
  ページが変わったので `metadata/publication/<id>/{artifact,decision,evidence}.json` の hash を再ピンした。
  **`decision.status` は `requires_review` のまま**（内容審査は owner の判断であり、本作業では行っていない）。
- `datasets/cannabinoid-platform-trends/data/processed/`: `trend_observations` 68 → 76 行
  （4 化合物の 5 年平均・ピーク・最新値・非ゼロ週・ゼロ週）。
  「Some temporal completeness fields are unavailable」の注記は 4 化合物から消えた。
- `docs/audits/*`（g2/g3/g4/g5/g6/g7、contract-ledger）を再生成: run 数 42 → 46。
- 旧 baseline run（`20261008T093228Z-google-trends-5y-baseline`）は **raw に残したまま**、
  どの化合物の引用元でもなくなった。

## 5. 制約・留意点

- **窓が 1 週ずれる**: 2026-10-15 収集分は `2021-10-10 〜 2026-10-11`、今回分は `2021-10-17 〜 2026-10-18`。
  同一窓の再現ではなく**別窓の観測**。相対 timeframe を絶対窓に固定できない制約（`docs/specs/gt-boundary-verification.md`）は未解決のまま。
- **水準を化合物間で比較しない**: Google Trends はクエリ単位の相対指数（0-100）。
  平均値の大小は需要の大小ではない（例: HHC 2.49 / THCV 7.43 は「HHC の方が低需要」を意味しない）。
  化合物間比較は共通スケール比較 run（`common-scale-*`）が担う。
- **欠測と 0 は別**: THCV は 262 週中 217 週が 0、HHC は 72 週が 0。これは `observed_zero`、
  collection failure ではない（L1 は `status=success` / `returned_count=262`）。
- **反復収集はしていない**: 1 化合物 1 run。Google Trends の non-determinism は未測定
  （AGENTS.md「Repeated Collection」）。再現性の確認は別途の反復 run が必要。
- **run_id の時刻**: THC run の `run_id` は `…T162500Z` だが、実際の収集時刻は
  `collection_started_at = 2026-10-23T16:03:58Z`（採番を先に行ったためのずれ）。
  実行時刻の正本は `run_metadata.json` の `collection_started_at` / `reference_time`。
- 12ヶ月系列の `THCV` / `THC-O` は引き続き「データなし」（Google Trends が閾値未満で系列を返さない）。
  今回の 5 年取得では THCV の系列が返ったため、**欠測は期間・正規化に依存する**ことが確認できた。

## 6. 検証

| 検査 | 結果 |
|---|---|
| `pytest -q` | 1464 passed / 4 skipped |
| `validation.cli gate-run`（4 run） | すべて PASS |
| `validation.cli validate-registries` | PASS |
| `validation.cli audit-new-runs` | 46 run、new=17、failures=0 |
| `validation.cli audit-publication` | findings=0（PC-7 の hash 再ピン後） |
| `docs/audits/*` 再生成 | すべて再現一致（freshness テスト） |
