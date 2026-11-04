# Issue: 3ヶ月 Google Trends run の metadata が日次データを `week` と記録する

**ID:** ISS-20261105-GT-031
**優先度:** P1 (High)
**ステータス:** RESOLVED (2026-11-05)
**対象:** `src/collection/adapters/google_trends/adapter.py`,
`src/collection/adapters/google_trends/boundary.py`,
`tests/collection/test_gt_granularity.py`
**リリース:** v1.14.4（本 issue の修正を含む）
**GitHub:** 未起票（ローカル記録。起票時にこの行へ追記する）

## 概要

Google Trends は `today 1-m` / `today 3-m` を日次系列で返すが、adapter は
request の timeframe に関係なく `temporal_provenance.granularity` を `week` と
記録していた。payload は日次 93 点、metadata は週次、という矛盾が run 記録に
残っている。

## 実測（読み取り専用）

| run | timeframe | 返却点 | 記録された granularity | 実際の間隔 |
|---|---|---|---|---|
| `20261104T175220Z-google-trends-cannabinoid-raw-collection` | `today 3-m` | 93 | `week` | 1 日 |
| `20261015T042849Z-google-trends-boundary-3m` | `today 3-m` | 93 | `week` | 1 日 |
| `20261015T042845Z-google-trends-boundary-1m` | `today 1-m` | 31 | `week` | 1 日 |
| `20261015T042853Z-google-trends-boundary-12m` | `today 12-m` | 53 | `week` | 7 日（正しい） |
| `20261015T042857Z-google-trends-boundary-5y` | `today 5-y` | 262 | `week` | 7 日（正しい） |

payload の `comparison_cbd-thc-thcnm.json` / `records_*.json` の日付はすべて
連続日であり、週次バケットではない。

## 影響範囲

- run metadata を読む下流（`audit-temporal`、被覆表、公開ページの
  「観測範囲」「点数」の説明）は、3ヶ月系列を週次と誤読しうる。
- 処理層は現在 `granularity` を分岐に使っていないため、既存の集計値は壊れて
  いない（`src/processing/gt_statistics.py` は点数と日付だけを使う）。
- 既存 raw の payload と run_metadata は変更しない。過去 run の誤記録は
  履歴として残し、本 issue と v1.14.4 の CHANGELOG で説明する。
- 3ヶ月 run の `2026-08-13 = 12`（孤立スパイク）は本 issue の対象外。

## 修正方針

1. granularity を request ではなく **返却系列のラベル間隔** で決める。
   連続日 = `day`、7日刻み = `week`。系列が短すぎる / 不規則な場合だけ
   timeframe の既定値（`now 7-d` / `today 1-m` / `today 3-m` = `day`、
   それ以外 = `week`）にフォールバックする。
2. `week_start` は `week` のときだけ `sunday`、`day` では `null`
   （`WEEK_START_UNEXPECTED` 警告を出さない）。
3. `boundary.py` の plan window / temporal も同じ規則を使う。
4. raw payload は一切書き換えない。過去 run の metadata は再発行しない。

## 受入条件

- [x] `today 3-m` の日次 payload で `granularity == "day"`、`week_start is None`
- [x] 回帰テスト（`tests/collection/test_gt_granularity.py`）:
      日次 93 点 → `day`、既存 12ヶ月 fixture → `week`、フォールバック規則
- [x] 既存 raw payload の SHA-256 が不変（本修正は metadata 生成のみ）
- [x] `make audit-snapshots` と `make test` が通る

## 関連

- `docs/specs/gt-boundary-verification.md`（boundary probe の metadata）
- `docs/specs/validation-framework.md` §26（snapshot scope）
- v1.14.4 CHANGELOG
