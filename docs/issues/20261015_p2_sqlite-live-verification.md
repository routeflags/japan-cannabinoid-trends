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

- [ ] ローカル検証手順（コマンドと期待出力）の文書化
- [ ] `record_lineage` 導入の要否決定
- [ ] raw との対応（run ↔ DB 行）の記録方法の決定
