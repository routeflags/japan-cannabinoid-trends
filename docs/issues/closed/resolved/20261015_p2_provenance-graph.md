# Issue: Provenance Graph（グラフ化 / PROV-O 変換）が未実装

**ID:** ISS-20261015-PRV-012
**優先度:** P2 (Medium)
**ステータス:** RESOLVED (2026-10-15)
**対象:** `src/storage/lineage.py`, `docs/specs/validation-framework.md` §18.3

## 概要

lineage 辺（run → artifact → transformation）は JSON の参照としてのみ表現されている。
グラフ DB・PROV-O 変換は未実装（仕様上も初期は JSON で足りるという判断）。

## 確認された観測

- manifest の `derived_from` と lineage 検査（`check_manifest_lineage`）は存在する。
- legacy 29 run は manifest が無く `lineage: unknown` として明示される。

## 影響

- 横断的な系譜の問い合わせ（どの研究が同じ raw に依存しているか等）が手作業になる。

## 対応方針

- 外部標準（PROV-O）への変換が必要になった時点で実装する。不要と判断するなら、その判断をここに記録して issue を閉じる。

## 完了条件

- [x] グラフ化の要否判断の記録（不要と判断。下記の証拠と将来 scope を記録）
- [x] 実装する場合は JSON lineage → グラフ / PROV-O の変換と検証（不要のため未実施）

## 解決記録（2026-10-15）: グラフ化は今は不要

本 vertical slice にグラフ DB・PROV-O 変換は不要と判断し、実装しない。判断の証拠:

- lineage 辺は JSON 参照として既に存在し、検査で担保されている:
  manifest の `derived_from` + `check_manifest_lineage`、transformation の入出力 +
  `check_transformation_lineage`、run → manifest 参照、派生宣言レジストリ
  (`processing.reproduce.DERIVATIONS`)。本スライスで transformation 生成記録
  （PRV-010）が加わり、run → artifact → transformation の鎖が JSON 上で完結した。
- 横断問い合わせ（どの研究が同じ raw に依存しているか）は既存関数で答えられる:
  `storage.lineage.trace_ancestors` / `check_catalog_lineage`（契約テスト
  `tests/storage/test_catalog.py` が固定）。グラフ DB を要する問い合わせは存在しない。
- 依存を増やさない: 第三者依存は cerberus のみ（`pyproject.toml`）が本リポジトリの
  方針。グラフ DB の導入は現時点で便益がなく方針に反する。
- 消費者不在: 公開・横断研究のいずれにも PROV-O を要求する相手は今いない
  （要求が出た時点で下記 scope で実装する）。

**将来の narrowed scope**: 具体的消費者の要求を trigger とし、JSON → PROV-O /
隣接 export のみ実装する。graph DB 依存は既存に無い限り持ち込まない。
収集 run の lineage が JSON 参照で表せなくなった場合も再評価する。
