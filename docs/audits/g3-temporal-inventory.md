# G3 Temporal Inventory（Phase 1）— 旧 run の期間指定の棚卸し

**日付:** 2026-10-13
**仕様:** `docs/plans/20261013c.md` §15 / §16 Phase 1（ローカル計画書）
**機械可読版:** [`g3-temporal-inventory.json`](./g3-temporal-inventory.json)（再生成: `python -m validation.cli audit-temporal`）
**非破壊:** 読取専用。全対象ファイルの sha256 を前後で比較し `raw_modified: false`。

---

## 1. 対象と方法

`datasets/**/run_metadata.json` 全 **29 件**（すべて既存・導入前。凍結リスト一致）。
各 run ディレクトリの metadata とペイロード JSON から、次を**事実として**抽出する。

- 期間指定（`timeframe` / `queries[].timeframe` / ペイロード内の `timeframe`。出典を記録）
- 基準日時（`collection_timestamp` / `collected_at` 等。出典を記録）
- 観測ラベル範囲（`data[].date` の最小・最大。出典を記録）
- 完全性・上限を判断できる証拠のフィールド名（`note` / `zero_status` / `rate_limit_429` / `no_data_keywords` 等）

分類（§15 の 4 状態。run の期間証拠に対する分類）:

| 分類 | 規則 | 結果 |
|---|---|---|
| `verified` | run 自身が絶対 bounds（`temporal_provenance.requested_*`）を持つ | 0 件 |
| `inferred` | 相対 timeframe が単一・整合し、基準日時がある | **29 件** |
| `ambiguous` | timeframe 証拠が複数ソースで不一致 | 0 件 |
| `unknown` | timeframe 証拠または基準日時がない | 0 件 |

## 2. 重要な制限（P1 準拠）

- 相対期間（`today 12-m` / `today 5-y`）は**絶対 window へ遡及変換しない**。
  全レコードで `resolved_absolute_window: null` + not-derived 理由を記録する
  （変換は推測であり、研究計画の正本を汚すため）。
- 観測ラベル範囲は「取得できた系列のラベル範囲」であり、期間全体の取得完了を
  意味しない。

## 3. 実例（§14 の検証用題材）

| run_id | timeframe | 基準日時 | 観測ラベル | 証拠 |
|---|---|---|---|---|
| `common-scale-missing-20261009` | `today 12-m` | 2026-10-09 | 2025-10-05 .. 2026-10-04（53点） | `note`、比較系列 |
| `20261002T064135Z-google-trends-nodata` | `today 12-m`（records_nodata.json） | 2026-10-02T06:41:35Z | なし（系列なし） | `no_data_keywords[THCV/THC-O]`（閾値未満の可能性） |

この 2 件は `coverage-run` の実例として使う: 前者は `partial`（terms は
observed_nonzero、0 点は below_threshold 候補）、後者は `missing`（terms は
`below_threshold`。**`observed_zero` には変換しない** — P7）。

## 4. 再現

```bash
.venv/bin/python -m validation.cli audit-temporal \
  --output docs/audits/g3-temporal-inventory.json
```

`tests/validation/test_temporal_inventory.py` が再計算一致・`raw_modified: false`・
29 件・遡及変換なしを機械的に強制する（スナップショットのドリフト検出）。
