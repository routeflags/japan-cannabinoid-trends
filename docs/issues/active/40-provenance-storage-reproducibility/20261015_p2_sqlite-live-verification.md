# Issue: SQLite 実データ（`trends.db`）の検証経路が無く、`record_lineage` 未導入

**ID:** ISS-20261015-ART-007  
**優先度:** P2 (Medium)  
**ステータス:** OPEN  
**対象:** `datasets/youtube-consistency/data/trends.db`（Git 管理外）, `datasets/youtube-consistency/schema/schema.sql`, `docs/specs/validation-framework.md` §17.3

## 概要

YouTube 一貫性研究の raw はローカル SQLite（`trends.db`）にあり、Git 管理外で CI も扱わない。
storage contract は SQLite 形式を宣言済み（`sqlite-trends-db-v1`）だが、実データの検証は
ローカル実施が必要で、`record_lineage` テーブル（run / artifact との対応）は導入されていない。

## 確認された観測

- `datasets/youtube-consistency/data/.gitignore` は `*` で、DB は追跡対象外。
- `schema/schema.sql` に `record_lineage` テーブルは無い。
- 当該 DB はデータを保持しているが、`runs.apify_dataset_id` を除いて Apify 側の実行記録との
  対応は記録されていない（ISS-20261015-PRV-013）。

## 影響

- DB の内容と raw（Apify dataset / CSV）の対応を機械検証できない。
- DB を再生成可能な派生物として扱うための前提（lineage）が欠けている。

## 対応方針

- ローカル専用の read-only 検証経路（schema 整合・表の存在・件数）を用意する。
- `record_lineage` の導入は実運用判断とし、導入する場合は schema 変更として記録する。
- DB を Git に入れない方針は維持する。

## 完了条件

- [x] ローカル検証手順（コマンドと期待出力）の文書化
- [x] `record_lineage` 導入の要否決定
- [~] raw との対応（run ↔ DB 行）の記録方法の決定

## 実装メモ（2026-10-15、OPEN のまま）

検証経路と `record_lineage` 判断は実装・文書化したが、run ↔ DB 行対応の
機械検証はクラウド証拠（ISS-20261015-PRV-013）待ちのため本 issue は
OPEN のまま残す。DB は Git に入れていない。外部 API は一切呼んでいない。

- 検証コマンド: `python3 -m storage.cli verify-trends-db`
  （`src/storage/cli.py`。既定 DB は `datasets/youtube-consistency/data/trends.db`。
  `SqliteReader` の `mode=ro` 接続のみを用いる read-only 検査で、期待表
  `runs` / `videos` / `run_videos`、期待ビュー `v_run_summary` /
  `v_video_appearance`、表ごとの行数、`record_lineage` 有無を JSON 報告する。
  DB 不在・非 DB・読み取り不可は traceback なしの exit 3。
  本 worktree に DB は無いため、不在時の優雅な失敗を実実行で確認済み）
- テスト: `tests/storage/test_verify_trends_db.py`（6 件。実 `schema.sql`
  を合成 DB に適用して期待表と突合するため、schema 変更時は検出される。
  実 DB は一切要求しない）
- 文書化: `datasets/youtube-consistency/README.md` に「ローカル検証」節を
  追加（コマンド・exit コード・出力形式例。形式例の値は観測値ではない旨を明示）
- `record_lineage` 決定: **導入見送り（deferred）**。理由は README 記載の
  とおり（空テーブルによる誤読防止／backfill 材料のクラウド証拠が未取得／
  推測で埋めない）。将来 migration 形（`record_lineage` の CREATE TABLE 概形＋
  `apify_dataset_id` ↔ 宣言突合の backfill 原則）も README に記録した。
  `schema.sql` は未変更。
- 検証: `python3 -m pytest tests/storage/test_verify_trends_db.py tests/storage/test_sqlite_reader.py tests/storage/test_storage_cli.py -q`

残りのオーナー作業: PRV-013 のクラウド証拠（actor input・run 対応）が
取得された後に migration を実施し、run ↔ DB 行対応の機械検証を通すこと。
