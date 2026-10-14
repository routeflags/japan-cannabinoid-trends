# Issue: ソース別の staging ドライバと `stage` CLI が未実装

**ID:** ISS-20261015-COL-017  
**優先度:** P1 (High)  
**ステータス:** OPEN  
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

- [ ] 対象ソースと payload 形式の決定
- [ ] ドライバ実装（plan / artifact / 実行事実の組立）と契約テスト
- [ ] `stage` CLI サブコマンドとドキュメント更新
