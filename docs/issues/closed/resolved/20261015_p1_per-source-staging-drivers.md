# Issue: ソース別の staging ドライバと `stage` CLI が未実装

**ID:** ISS-20261015-COL-017  
**優先度:** P1 (High)  
**ステータス:** RESOLVED (2026-10-15)  
**対象:** `src/collection/core/pipeline.py`（`stage_run` は実装済み）, `src/collection/core/cli.py`, `docs/specs/collection-pipeline.md` §3.3

## 概要

- 2026-10-15 に外部 collector の産出側（`stage_run`）を実装したが、ソース別ドライバは無い。

## 確認された観測

- `collection.core.pipeline.stage_run` は `CollectedArtifact[]` + 実行事実の宣言を受け取り、
  `.staging/<run-id>/` を書く（テスト付き）。
- `collection.core.cli` のサブコマンドは `collect` / `adopt` / `compile-window` のみで
  `stage` は無い。
- 2026-10-14 の YouTube dataset CSV 7 件（`~/Downloads/dataset_youtube-scraper_*.csv`）は
  このドライバが無いため、パイプラインに乗せられていない。

## 影響

- ダウンロード済みデータを契約に乗せるのに、毎回その場のスクリプトが必要になり、
  再現性とレビュー容易性が下がる。
- plan（query registry 参照・窓 compile を含む）と実行事実の組立がソースごとにバラつく。

## 対応方針

- 対象ソースと payload 形式（CSV のまま / JSON 再エクスポート / MCP 応答の記録）を決める。
- ドライバは「plan と artifact 宣言を組み立てる」役に限定し、契約の検査は `stage_run` +
  `adopt`（L1）に任せる（規則を 2 実装しない）。
- 宣言の入力形式（CLI 引数 / 宣言ファイル）を決めてから実装する。

## 完了条件

- [x] 対象ソースと payload 形式の決定
- [x] ドライバ実装（plan / artifact / 実行事実の組立）と契約テスト
- [x] `stage` CLI サブコマンドとドキュメント更新

## 対応記録（2026-10-15）

- 決定: 対象は YouTube（Apify dataset export）、payload は **CSV のまま**
  （メンテナの決定。JSON 再エクスポートなし）。
- 実装: `src/collection/core/staging.py`（宣言ファイル `staging-declaration-v1`
  → plan / artifact / 実行事実の組立 → `stage_run`。宣言レベルの失敗は exit 2 で
  何も staging しない）と `stage` CLI（`src/collection/core/cli.py`）。
  keyword → `query_id` は宣言入力で、payload からは推定しない（テストで固定）。
- 依存: `ISS-20261015-ART-009`（CSV reader + `youtube-dataset-csv-v1`）を
  同一作業で解決済み（record_count の導出に必要）。
- 契約テスト: `tests/collection/test_staging_driver.py`（14 件）、
  CLI 5 件（`tests/collection/test_collection_cli.py`）。
- 実データ rehearsal（リポジトリ外 scratch workspace）: 2026-10-14 ダウンロードの
  実 export 7 件を stage（7/7）→ adopt（7/7）→ `validate_full
  (verify_artifacts=True)` 厳格 valid → `audit-new-runs` new=7 / failures=0。
  payload は原本と byte 一致。記録と確認依頼:
  `docs/reports/20261015b-youtube-csv-staging-driver.md`。
- 未実施: 7 件の**実採用**（窓・date_filter・実行 status 等の宣言事実の確認が
  先。同レポート §5）。仕様: `docs/specs/collection-pipeline.md` §3.4。
